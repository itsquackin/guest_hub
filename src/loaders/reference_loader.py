"""Reference table loader.

Loads the room_types.tsv and special_requests.tsv lookup tables from the
configured reference directory into in-memory dictionaries.
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.utils.constants import (
    ROOM_TYPE_CODE_COL,
    ROOM_TYPE_DESC_COL,
    SPECIAL_CODE_COL,
    SPECIAL_DESC_COL,
)
from src.utils.file_utils import read_tsv

logger = logging.getLogger(__name__)


def load_room_type_map(reference_dir: str | Path) -> dict[str, str]:
    """Load room_types.tsv into a ``{code: description}`` dict.

    Returns an empty dict when the file is missing or has no data rows.
    """
    path = Path(reference_dir) / "room_types.tsv"
    if not path.exists():
        logger.warning("room_types.tsv not found at: %s", path)
        return {}
    rows = read_tsv(path)
    mapping = {
        r[ROOM_TYPE_CODE_COL].strip().upper(): r[ROOM_TYPE_DESC_COL].strip()
        for r in rows
        if r.get(ROOM_TYPE_CODE_COL, "").strip()
    }
    logger.info("Loaded %d room type codes from %s", len(mapping), path.name)
    return mapping


def load_special_request_map(reference_dir: str | Path) -> dict[str, str]:
    """Load special_requests.tsv into a ``{code: description}`` dict.

    Returns an empty dict when the file is missing or has no data rows.
    """
    path = Path(reference_dir) / "special_requests.tsv"
    if not path.exists():
        logger.warning("special_requests.tsv not found at: %s", path)
        return {}
    rows = read_tsv(path)
    mapping = {
        r[SPECIAL_CODE_COL].strip().upper(): r[SPECIAL_DESC_COL].strip()
        for r in rows
        if r.get(SPECIAL_CODE_COL, "").strip()
    }
    logger.info("Loaded %d special request codes from %s", len(mapping), path.name)
    return mapping


def load_all_reference_maps(
    reference_dir: str | Path,
) -> tuple[dict[str, str], dict[str, str]]:
    """Load all reference tables and return ``(room_type_map, special_request_map)``."""
    room_type_map = load_room_type_map(reference_dir)
    special_request_map = load_special_request_map(reference_dir)
    return room_type_map, special_request_map
