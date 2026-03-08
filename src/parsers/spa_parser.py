"""Spa PDF parser.

Extracts appointment rows from spa calendar/itinerary PDFs.
Tries pdfplumber first; falls back to a built-in PDF stream reader
when pdfplumber is unavailable (e.g. missing system cryptography libs).

The parser is intentionally permissive — messy or unrecognized rows are
logged and skipped rather than raising exceptions.
"""
from __future__ import annotations

import logging
import re
import zlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.cleaners.dates import parse_date
from src.cleaners.nulls import normalize_null
from src.cleaners.names import split_full_name, build_match_name_key, build_full_name_clean
from src.utils.id_utils import make_source_row_id

logger = logging.getLogger(__name__)

# ── Optional pdfplumber import ────────────────────────────────────────────────

try:
    import pdfplumber
    _PDFPLUMBER_OK = True
except BaseException:  # broad catch — pyo3 PanicException is not an Exception subclass
    pdfplumber = None  # type: ignore[assignment]
    _PDFPLUMBER_OK = False
    logger.debug("pdfplumber not available; using built-in PDF text reader")


# ── Raw data class ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class SpaAppointmentRaw:
    """Raw spa appointment representation before canonical standardization."""
    source_file_name: str
    source_row_id: str
    guest_name_raw: str
    service_date_raw: str
    service_time_raw: str
    service_name_raw: str
    duration_raw: str = ""
    therapist_raw: str = ""


# ── Built-in minimal PDF text extractor ──────────────────────────────────────

_PDF_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
_TJ_OP = re.compile(r"\(([^)]*)\)\s*Tj")
_TJ_ARRAY = re.compile(r"\(([^)]*)\)")


def _decode_stream(raw: bytes) -> str:
    """Attempt to decode a PDF content stream."""
    try:
        return zlib.decompress(raw).decode("latin-1", errors="replace")
    except Exception:
        pass
    try:
        return raw.decode("latin-1", errors="replace")
    except Exception:
        return ""


def _extract_text_builtin(pdf_path: Path) -> str:
    """Extract plain text from a PDF using stdlib only.

    Uses regex-based extraction of PDF text operators (Tj / TJ).
    Handles FlateDecode-compressed streams.
    """
    try:
        raw_pdf = pdf_path.read_bytes()
    except OSError as exc:
        logger.error("Cannot read PDF %s: %s", pdf_path, exc)
        return ""

    lines: list[str] = []
    for m in _PDF_STREAM.finditer(raw_pdf):
        stream_bytes = m.group(1)
        text = _decode_stream(stream_bytes)
        # Extract strings from Tj and TJ operators
        for tj in _TJ_OP.finditer(text):
            lines.append(tj.group(1))
        for arr in _TJ_ARRAY.finditer(text):
            val = arr.group(1).strip()
            if val:
                lines.append(val)

    return "\n".join(lines)


# ── Text-based appointment row parser ─────────────────────────────────────────

# Common date patterns found in spa calendar exports
_DATE_RE = re.compile(
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\w+ \d{1,2},?\s*\d{4}|\d{4}-\d{2}-\d{2})\b"
)
_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b")
_DURATION_RE = re.compile(r"\b(\d{2,3})\s*(?:min|mins|minutes?)\b", re.IGNORECASE)


def _parse_text_lines(
    lines: list[str],
    file_name: str,
) -> list[SpaAppointmentRaw]:
    """Attempt to extract appointments from free-form text lines.

    Strategy: look for lines containing a date and a guest name candidate.
    Spa calendar exports vary widely; this covers a common tabular format.
    """
    records: list[SpaAppointmentRaw] = []
    row_idx = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip short, blank, or header-like lines
        if len(line) < 5 or line.lower() in {"guest", "service", "date", "time", "therapist"}:
            i += 1
            continue

        # Try to detect a date on this line or the next
        date_match = _DATE_RE.search(line)
        time_match = _TIME_RE.search(line)

        if date_match:
            date_raw = date_match.group(1)
            time_raw = time_match.group(1) if time_match else ""

            # Look ahead for guest name and service
            guest_raw = ""
            service_raw = ""
            duration_raw = ""

            # Scan adjacent lines for name/service info
            for j in range(max(0, i - 2), min(len(lines), i + 4)):
                nearby = lines[j].strip()
                if not nearby or nearby == line:
                    continue
                dm = _DURATION_RE.search(nearby)
                if dm:
                    duration_raw = dm.group(0)
                # Heuristic: lines without digits are likely names or services
                if not any(ch.isdigit() for ch in nearby) and len(nearby) > 2:
                    if not guest_raw:
                        guest_raw = nearby
                    elif not service_raw:
                        service_raw = nearby

            if guest_raw:
                row_idx += 1
                records.append(
                    SpaAppointmentRaw(
                        source_file_name=file_name,
                        source_row_id=make_source_row_id(file_name, row_idx),
                        guest_name_raw=guest_raw,
                        service_date_raw=date_raw,
                        service_time_raw=time_raw,
                        service_name_raw=service_raw,
                        duration_raw=duration_raw,
                    )
                )

        i += 1

    return records


def _parse_via_pdfplumber(pdf_path: Path) -> list[SpaAppointmentRaw]:
    """Extract appointment rows using pdfplumber."""
    file_name = pdf_path.name
    records: list[SpaAppointmentRaw] = []
    row_idx = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Try table extraction first
            tables = page.extract_tables()
            for table in tables:
                for raw_row in table:
                    if not raw_row:
                        continue
                    cells = [c or "" for c in raw_row]
                    if len(cells) < 2:
                        continue
                    # Heuristic column order: date/time, guest, service, duration
                    row_text = " | ".join(cells)
                    date_m = _DATE_RE.search(row_text)
                    time_m = _TIME_RE.search(row_text)
                    dur_m = _DURATION_RE.search(row_text)

                    guest_raw = ""
                    service_raw = ""
                    # Look for name-like cells (no digits, > 2 chars)
                    for cell in cells:
                        cell = cell.strip()
                        if not any(ch.isdigit() for ch in cell) and len(cell) > 2:
                            if not guest_raw:
                                guest_raw = cell
                            elif not service_raw:
                                service_raw = cell

                    if guest_raw and (date_m or time_m):
                        row_idx += 1
                        records.append(
                            SpaAppointmentRaw(
                                source_file_name=file_name,
                                source_row_id=make_source_row_id(file_name, row_idx),
                                guest_name_raw=guest_raw,
                                service_date_raw=date_m.group(1) if date_m else "",
                                service_time_raw=time_m.group(1) if time_m else "",
                                service_name_raw=service_raw,
                                duration_raw=dur_m.group(0) if dur_m else "",
                            )
                        )

            # Fall back to text extraction for pages with no tables
            if not tables:
                text = page.extract_text() or ""
                page_records = _parse_text_lines(
                    text.splitlines(), file_name
                )
                # Re-index
                for rec in page_records:
                    row_idx += 1
                    records.append(
                        SpaAppointmentRaw(
                            source_file_name=rec.source_file_name,
                            source_row_id=make_source_row_id(file_name, row_idx),
                            guest_name_raw=rec.guest_name_raw,
                            service_date_raw=rec.service_date_raw,
                            service_time_raw=rec.service_time_raw,
                            service_name_raw=rec.service_name_raw,
                            duration_raw=rec.duration_raw,
                        )
                    )

    return records


# ── Public API ────────────────────────────────────────────────────────────────

def parse_spa_pdf_file(pdf_path: Path) -> list[SpaAppointmentRaw]:
    """Extract appointment-like rows from a spa itinerary PDF.

    Uses pdfplumber when available; falls back to a built-in stream reader.
    Returns an empty list on unrecoverable errors so the pipeline continues.
    """
    file_name = pdf_path.name
    logger.info("Parsing spa PDF: %s", file_name)

    if _PDFPLUMBER_OK:
        try:
            records = _parse_via_pdfplumber(pdf_path)
            logger.info(
                "Extracted %d spa appointment rows from %s (pdfplumber)",
                len(records), file_name,
            )
            return records
        except Exception as exc:
            logger.warning(
                "pdfplumber failed for %s (%s); falling back to built-in reader",
                file_name, exc,
            )

    # Built-in fallback
    text = _extract_text_builtin(pdf_path)
    records = _parse_text_lines(text.splitlines(), file_name)
    logger.info(
        "Extracted %d spa appointment rows from %s (built-in reader)",
        len(records), file_name,
    )
    return records
