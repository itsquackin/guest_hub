"""Room source file loader.

Discovers XML files in the configured raw/rooms directory and returns
their paths for downstream parsing.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.utils.constants import ROOM_FILE_GLOB
from src.utils.file_utils import find_files

logger = logging.getLogger(__name__)


def find_room_files(directory: str | Path) -> list[Path]:
    """Return a sorted list of room XML files in *directory*.

    Logs a warning when no files are found.
    """
    files = find_files(directory, ROOM_FILE_GLOB)
    if not files:
        logger.warning("No room XML files found in: %s", directory)
    else:
        logger.info("Found %d room file(s) in: %s", len(files), directory)
    return files


def load_room_files(directory: str | Path) -> list[Path]:
    """Return validated, non-empty room XML paths from *directory*."""
    paths = find_room_files(directory)
    readable = []
    for p in paths:
        if p.is_file() and p.stat().st_size > 0:
            logger.debug("Queued room file: %s", p.name)
            readable.append(p)
        else:
            logger.warning("Skipping empty or unreadable room file: %s", p)
    return readable
