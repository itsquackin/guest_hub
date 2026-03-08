"""Special request code parsing utilities.

Thin wrapper kept separate so the specials splitting logic can be
tested and imported independently from room_types_parser.
"""
from __future__ import annotations

from src.cleaners.codes import split_specials_string


def parse_specials_field(raw: str | None) -> list[str]:
    """Split a raw specials string into individual uppercased code tokens.

    Delegates to :func:`src.cleaners.codes.split_specials_string`.
    Handles commas, semicolons, slashes, pipes, and plus signs as delimiters.
    """
    return split_specials_string(raw)
