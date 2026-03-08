"""Spa source file loader.

Discovers PDF files in the configured raw/spa directory.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.utils.constants import SPA_FILE_GLOB
from src.utils.file_utils import find_files

logger = logging.getLogger(__name__)


def find_spa_files(directory: str | Path) -> list[Path]:
    """Return a sorted list of spa PDF files in *directory*."""
    files = find_files(directory, SPA_FILE_GLOB)
    if not files:
        logger.warning("No spa PDF files found in: %s", directory)
    else:
        logger.info("Found %d spa file(s) in: %s", len(files), directory)
    return files


def load_spa_files(directory: str | Path) -> list[Path]:
    """Return validated, non-empty spa PDF paths from *directory*."""
    paths = find_spa_files(directory)
    readable = []
    for p in paths:
        if p.is_file() and p.stat().st_size > 0:
            logger.debug("Queued spa file: %s", p.name)
            readable.append(p)
        else:
            logger.warning("Skipping empty or unreadable spa file: %s", p)
    return readable
