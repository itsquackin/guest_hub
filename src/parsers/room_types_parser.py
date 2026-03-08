"""Room type and special request reference table parsers."""
from __future__ import annotations

import logging
from pathlib import Path

from src.utils.file_utils import read_tsv
from src.utils.constants import (
    ROOM_TYPE_CODE_COL,
    ROOM_TYPE_DESC_COL,
    SPECIAL_CODE_COL,
    SPECIAL_DESC_COL,
)

logger = logging.getLogger(__name__)


def parse_room_types_tsv(path: str | Path) -> dict[str, str]:
    """Parse room_types.tsv and return a ``{code: description}`` dict."""
    try:
        rows = read_tsv(path)
    except FileNotFoundError:
        logger.error("room_types.tsv not found: %s", path)
        return {}
    mapping: dict[str, str] = {}
    for row in rows:
        code = row.get(ROOM_TYPE_CODE_COL, "").strip().upper()
        desc = row.get(ROOM_TYPE_DESC_COL, "").strip()
        if code:
            mapping[code] = desc
    return mapping


def parse_specials_tsv(path: str | Path) -> dict[str, str]:
    """Parse special_requests.tsv and return a ``{code: description}`` dict."""
    try:
        rows = read_tsv(path)
    except FileNotFoundError:
        logger.error("special_requests.tsv not found: %s", path)
        return {}
    mapping: dict[str, str] = {}
    for row in rows:
        code = row.get(SPECIAL_CODE_COL, "").strip().upper()
        desc = row.get(SPECIAL_DESC_COL, "").strip()
        if code:
            mapping[code] = desc
    return mapping
