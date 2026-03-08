"""Preserved legacy spa calendar converter placeholder.

This module remains in the repository as a first-class legacy asset while the new
`src/parsers/spa_parser.py` pipeline parser is implemented.
"""

from __future__ import annotations

from pathlib import Path


def convert_spa_calendar_pdf_to_excel(pdf_path: Path, output_path: Path) -> Path:
    """Legacy conversion entry point preserved for backward compatibility.

    TODO: wire this wrapper to the legacy conversion implementation/script.
    """
    _ = pdf_path
    return output_path
