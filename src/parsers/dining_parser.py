"""Dining CSV parser.

Reads dining reservation/visit CSV files, strips all revenue-style columns
(per business rules), and returns raw row records for canonicalization.

Revenue columns are defined in config/column_maps.yaml and mirrored in
REMOVED_REVENUE_COLUMNS below.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.id_utils import make_source_row_id
logger = logging.getLogger(__name__)

# ── Revenue columns to strip (business rule: locked) ─────────────────────────

REMOVED_REVENUE_COLUMNS: frozenset[str] = frozenset({
    "Experience Title",
    "Experience Price Type",
    "Experience Price",
    "Additional Payments",
    "Additional Payments Subtotal",
    "Experience Gratuity",
    "POS Subtotal",
    "POS Tax",
    "POS Service Charges",
    "POS Gratuity",
    "POS Paid",
    "POS Due",
    "Prepayment Method",
    "Prepayment Status",
    "Prepaid Experience Total Paid",
    "Total Gratuity",
    "Total Tax",
    "Experience Total Sales",
    "Experience Total Sales with Gratuity",
    "Total Revenue",
    "Total Revenue with Gratuity",
})

# ── Column alias map (canonical name → possible CSV headers, case-insensitive) ─

_COLUMN_ALIASES: dict[str, list[str]] = {
    "visit_date":           ["date", "visit date", "reservation date"],
    "visit_time":           ["time", "visit time", "reservation time"],
    "guest_name_raw":       ["guest name", "name", "guest"],
    "first_name":           ["first name", "first"],
    "last_name":            ["last name", "last", "surname"],
    "phone_raw":            ["phone", "phone number", "tel", "telephone"],
    "party_size":           ["party size", "covers", "guests", "pax"],
    "dining_status":        ["status", "reservation status", "visit status"],
    "table_raw":            ["table", "table number", "table #"],
    "dining_area":          ["area", "section", "dining area", "room"],
    "booking_source":       ["booking source", "source", "channel"],
    "server_name":          ["server", "waiter", "staff", "host"],
    "guest_requests_raw":   ["guest requests", "requests", "special requests"],
    "visit_notes_raw":      ["notes", "visit notes", "comments"],
    "reservation_tags_raw": ["reservation tags", "tags"],
    "guest_tags_raw":       ["guest tags", "guest labels"],
    "completed_visits":     ["completed visits", "visit count", "visits"],
}


@dataclass(slots=True)
class DiningVisitRaw:
    """Raw dining visit record retaining only non-revenue fields."""
    source_file_name: str
    source_row_id: str
    # All retained CSV fields stored in a dict to allow flexible column handling
    retained: dict[str, str] = field(default_factory=dict)


def _build_alias_lookup(headers: list[str]) -> dict[str, str]:
    """Map CSV header names (lowercased) to canonical field names.

    Returns a dict: ``{csv_header_lower: canonical_name}``.
    """
    lower_headers = {h.strip().lower(): h for h in headers}
    lookup: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_headers:
                original = lower_headers[alias.lower()]
                lookup[original] = canonical
                break
    return lookup


def _is_revenue_column(header: str) -> bool:
    """Return True if this header matches a known revenue column."""
    return header.strip() in REMOVED_REVENUE_COLUMNS


def parse_dining_csv_file(csv_path: Path) -> list[DiningVisitRaw]:
    """Parse a dining CSV into a list of retained non-revenue raw records.

    Steps:
    1. Read all rows via csv.DictReader.
    2. Identify and strip all revenue-style columns.
    3. Map remaining columns to canonical names where aliases match.
    4. Return as DiningVisitRaw records.
    """
    file_name = csv_path.name
    logger.info("Parsing dining CSV: %s", file_name)

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                logger.warning("No headers found in %s", file_name)
                return []
            headers = list(reader.fieldnames)
            all_rows = list(reader)
    except (OSError, csv.Error) as exc:
        logger.error("Failed to read dining CSV %s: %s", file_name, exc)
        return []

    # Identify revenue columns to drop
    revenue_headers = {h for h in headers if _is_revenue_column(h)}
    if revenue_headers:
        logger.info(
            "Dropping %d revenue column(s) from %s: %s",
            len(revenue_headers), file_name, sorted(revenue_headers),
        )

    retained_headers = [h for h in headers if h not in revenue_headers]
    alias_lookup = _build_alias_lookup(retained_headers)

    records: list[DiningVisitRaw] = []
    for idx, row in enumerate(all_rows, start=1):
        retained: dict[str, str] = {}
        for h in retained_headers:
            val = (row.get(h) or "").strip()
            canonical = alias_lookup.get(h, h)  # use canonical name if known
            retained[canonical] = val

        records.append(
            DiningVisitRaw(
                source_file_name=file_name,
                source_row_id=make_source_row_id(file_name, idx),
                retained=retained,
            )
        )

    logger.info("Parsed %d dining records from %s", len(records), file_name)
    return records
