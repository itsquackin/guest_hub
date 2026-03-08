"""Spa PDF parser.

Extracts guest appointment data from SpaSoft Client Itinerary PDFs.
Tries pdfplumber first; falls back to a built-in PDF stream reader
when pdfplumber is unavailable (e.g. missing system cryptography libs).

SpaSoft itinerary format
------------------------
Each page contains blocks structured as::

    Guest: [Salutation] LastName FirstName
    DayOfWeek, Month DD, YYYY
    SPA  HH:MM AM  Service Name (60 Minutes)
    SPA  HH:MM AM  Another Service (90 Minutes)

The parser is intentionally permissive — messy or unrecognized rows are
logged and skipped rather than raising exceptions.
"""
from __future__ import annotations

import logging
import re
import zlib
from dataclasses import dataclass
from pathlib import Path

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


# ── SpaSoft-specific patterns ─────────────────────────────────────────────────

# "Guest: Mr. Smith John"  →  group(1) = everything after "Guest:"
_GUEST_LINE_RE = re.compile(r"^Guest:\s*(.+)$", re.IGNORECASE)

# "Friday, January 23, 2026"  or  "Friday, January 3, 2026"
_DATE_LINE_RE = re.compile(
    r"^[A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},?\s*\d{4}"
)

# "SPA  10:00 AM  Deep Tissue Massage (60 Minutes)"
_APPT_LINE_RE = re.compile(
    r"^SPA\s+(\d{1,2}:\d{2}\s+[AP]M)\s+(.+)$", re.IGNORECASE
)

# Duration inside service name: "(60 Minutes)", "(60 Min)"
_DURATION_RE = re.compile(r"\((\d+)\s*[Mm]in[^)]*\)")

_SALUTATIONS = ("Ms. ", "Mrs. ", "Mr. ", "Dr. ", "Miss ")


def _remove_salutation(name: str) -> str:
    for sal in _SALUTATIONS:
        if name.startswith(sal):
            return name[len(sal):]
    return name


def _parse_spasof_guest_name(raw: str) -> str:
    """Parse 'Guest: [Salutation] LastName FirstName' → 'FirstName LastName'.

    SpaSoft exports last name first, so we reverse the order so downstream
    name cleaners (which expect 'First Last') work correctly.
    """
    name = _remove_salutation(raw.strip())
    parts = name.split()
    if len(parts) == 0:
        return ""
    if len(parts) == 1:
        return parts[0]
    # SpaSoft: first token = last name, remainder = first name
    last = parts[0]
    first = " ".join(parts[1:])
    return f"{first} {last}"


# ── SpaSoft text line parser ──────────────────────────────────────────────────

def _parse_spasof_text(text: str, file_name: str) -> list[SpaAppointmentRaw]:
    """Parse SpaSoft itinerary text into SpaAppointmentRaw records.

    Walks lines looking for Guest / Date / SPA-appointment triples.
    """
    records: list[SpaAppointmentRaw] = []
    row_idx = 0
    current_guest = ""
    current_date = ""

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        guest_m = _GUEST_LINE_RE.match(line)
        if guest_m:
            current_guest = _parse_spasof_guest_name(guest_m.group(1))
            current_date = ""
            continue

        if current_guest and _DATE_LINE_RE.match(line):
            current_date = line
            continue

        if current_guest and current_date:
            appt_m = _APPT_LINE_RE.match(line)
            if appt_m:
                time_raw = appt_m.group(1).strip()
                service_raw = appt_m.group(2).strip()
                dur_m = _DURATION_RE.search(service_raw)
                duration_raw = f"{dur_m.group(1)} min" if dur_m else ""
                row_idx += 1
                records.append(
                    SpaAppointmentRaw(
                        source_file_name=file_name,
                        source_row_id=make_source_row_id(file_name, row_idx),
                        guest_name_raw=current_guest,
                        service_date_raw=current_date,
                        service_time_raw=time_raw,
                        service_name_raw=service_raw,
                        duration_raw=duration_raw,
                    )
                )

    return records


# ── Built-in minimal PDF text extractor ──────────────────────────────────────

_PDF_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
_TJ_OP = re.compile(r"\(([^)]*)\)\s*Tj")
_TJ_ARRAY = re.compile(r"\(([^)]*)\)")


def _decode_stream(raw: bytes) -> str:
    """Attempt to decode a PDF content stream."""
    try:
        return zlib.decompress(raw).decode("latin-1", errors="replace")
    except Exception:
        try:
            return raw.decode("latin-1", errors="replace")
        except Exception:
            return ""


def _extract_text_builtin(pdf_path: Path) -> str:
    """Extract plain text from a PDF using stdlib only."""
    try:
        raw_pdf = pdf_path.read_bytes()
    except OSError as exc:
        logger.error("Cannot read PDF %s: %s", pdf_path, exc)
        return ""

    lines: list[str] = []
    for m in _PDF_STREAM.finditer(raw_pdf):
        stream_bytes = m.group(1)
        text = _decode_stream(stream_bytes)
        for tj in _TJ_OP.finditer(text):
            lines.append(tj.group(1))
        for arr in _TJ_ARRAY.finditer(text):
            val = arr.group(1).strip()
            if val:
                lines.append(val)

    return "\n".join(lines)


# ── pdfplumber extraction ─────────────────────────────────────────────────────

def _parse_via_pdfplumber(pdf_path: Path) -> list[SpaAppointmentRaw]:
    """Extract SpaSoft appointment rows using pdfplumber text extraction."""
    file_name = pdf_path.name
    all_text_lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text_lines.extend(text.splitlines())

    return _parse_spasof_text("\n".join(all_text_lines), file_name)


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
    records = _parse_spasof_text(text, file_name)
    logger.info(
        "Extracted %d spa appointment rows from %s (built-in reader)",
        len(records), file_name,
    )
    return records
