"""Dining CSV parser stubs.

Parses dining reservations/visits while omitting revenue-only fields for this project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REMOVED_REVENUE_COLUMNS = {
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
}


@dataclass(slots=True)
class DiningVisitRaw:
    """Raw dining visit record retained for canonicalization."""

    source_file_name: str
    source_row_id: str
    guest_name_raw: str
    visit_date_raw: str
    visit_time_raw: str
    phone_raw: str | None


def parse_dining_csv_file(csv_path: Path) -> list[DiningVisitRaw]:
    """Parse a dining CSV into retained non-revenue raw records.

    TODO: use csv.DictReader and prune removed revenue columns.
    """
    _ = csv_path
    return []
