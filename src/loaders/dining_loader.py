"""Dining source file loader.

Discovers CSV files in the configured raw/dining directory.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.utils.constants import DINING_FILE_GLOB
from src.utils.file_utils import find_files

logger = logging.getLogger(__name__)


def find_dining_files(directory: str | Path) -> list[Path]:
    """Return a sorted list of dining CSV files in *directory*."""
    files = find_files(directory, DINING_FILE_GLOB)
    if not files:
        logger.warning("No dining CSV files found in: %s", directory)
    else:
        logger.info("Found %d dining file(s) in: %s", len(files), directory)
    return files


def load_dining_files(directory: str | Path) -> list[Path]:
    """Return validated, non-empty dining CSV paths from *directory*."""
    paths = find_dining_files(directory)
    readable = []
    for p in paths:
        if p.is_file() and p.stat().st_size > 0:
            logger.debug("Queued dining file: %s", p.name)
            readable.append(p)
        else:
            logger.warning("Skipping empty or unreadable dining file: %s", p)
    return readable
