#!/usr/bin/env python3
"""Legacy spa calendar converter entry point.

Wraps the preserved spa_calendar_converter script so it can be run
independently of the main pipeline.

Usage::

    python run_spa_legacy.py <input_pdf> <output_excel>

Example::

    python run_spa_legacy.py data/raw/spa/calendar.pdf outputs/spa_calendar.xlsx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legacy spa calendar PDF → Excel converter"
    )
    parser.add_argument("input_pdf", help="Path to the spa calendar PDF")
    parser.add_argument("output_excel", help="Path for the Excel output file")
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    from src.utils.logging_utils import configure_logging, get_logger
    configure_logging("config/logging.yaml", level=args.log_level)
    logger = get_logger("run_spa_legacy")

    input_path = Path(args.input_pdf)
    output_path = Path(args.output_excel)

    if not input_path.exists():
        logger.error("Input PDF not found: %s", input_path)
        return 1

    from src.legacy.spa_calendar_converter import convert_spa_calendar_pdf_to_excel
    try:
        result = convert_spa_calendar_pdf_to_excel(input_path, output_path)
        logger.info("Legacy conversion complete: %s", result)
        return 0
    except Exception as exc:
        logger.error("Legacy conversion failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
