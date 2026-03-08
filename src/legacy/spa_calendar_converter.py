"""Preserved legacy spa calendar converter.

This module remains in the repository as a first-class legacy asset.
It converts spa itinerary PDF exports to Excel workbooks.

The new pipeline parser (src/parsers/spa_parser.py) uses the same
extraction logic but outputs canonical SpaAppointmentRaw records
instead of writing directly to Excel.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.parsers.spa_parser import parse_spa_pdf_file
from src.transforms.spa_standardize import standardize_spa_file
from src.transforms.shared_fields import make_load_timestamp

logger = logging.getLogger(__name__)


def convert_spa_calendar_pdf_to_excel(pdf_path: Path, output_path: Path) -> Path:
    """Convert a spa calendar PDF to an Excel workbook.

    Extracts appointments using the pipeline spa parser and writes them to
    an Excel file using openpyxl.  Creates parent directories as needed.

    Args:
        pdf_path: Path to the spa itinerary PDF.
        output_path: Desired path for the output Excel file.

    Returns:
        The resolved path to the written Excel file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Legacy spa conversion: %s → %s", pdf_path.name, output_path.name)

    # Parse and standardize
    raw_records = parse_spa_pdf_file(Path(pdf_path))
    canonical_rows = standardize_spa_file(raw_records, load_timestamp=make_load_timestamp())

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = "Spa Appointments"

        if not canonical_rows:
            ws.append(["No appointments extracted"])
            wb.save(output_path)
            logger.warning("No appointments found in %s", pdf_path.name)
            return output_path

        import dataclasses
        headers = [f.name for f in dataclasses.fields(canonical_rows[0])]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for row in canonical_rows:
            values = []
            for h in headers:
                val = getattr(row, h)
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                values.append(val)
            ws.append(values)

        wb.save(output_path)
        logger.info(
            "Legacy conversion complete: %d appointments → %s",
            len(canonical_rows), output_path.name,
        )

    except ImportError:
        # openpyxl not available — write CSV instead
        import csv
        import dataclasses
        csv_path = output_path.with_suffix(".csv")
        headers = [f.name for f in dataclasses.fields(canonical_rows[0])]
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=headers)
            writer.writeheader()
            for row in canonical_rows:
                d = dataclasses.asdict(row)
                for k, v in d.items():
                    if isinstance(v, list):
                        d[k] = "; ".join(str(x) for x in v)
                writer.writerow(d)
        logger.info("openpyxl not available — wrote CSV: %s", csv_path)
        return csv_path

    return output_path
