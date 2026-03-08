"""Exact name/date matching.

Links activity records to room guest stays using exact normalized name
comparison plus date-window filtering.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.matching.stay_window import is_within_stay_window
from src.utils.constants import DEFAULT_DATE_TOLERANCE_DAYS, MATCH_EXACT_NAME_DATE


@dataclass(slots=True)
class ExactMatchCandidate:
    """Activity candidate presented for exact matching against room guest rows."""
    guest_id: str
    match_name_key: str
    activity_date: date


@dataclass(slots=True)
class RoomStayContext:
    """Room guest stay context used for date-window filtering."""
    guest_id: str
    match_name_key: str
    arrival_date: date
    departure_date: date


@dataclass(slots=True)
class ExactMatchResult:
    """Result of a successful exact name + date-window match."""
    stay: RoomStayContext
    method: str = MATCH_EXACT_NAME_DATE
    score: float = 1.0
    match_flag_fuzzy: bool = False
    matched_within_stay_window: bool = True


def match_exact_name_date(
    candidate: ExactMatchCandidate,
    stays: list[RoomStayContext],
    tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
) -> ExactMatchResult | None:
    """Find an exact name + date-window match.

    Returns the first stay whose match_name_key equals the candidate's
    and whose stay window (± tolerance) contains the activity_date.
    Returns None when no match is found.

    Explainability: the returned ExactMatchResult carries method, score=1.0,
    and match_flag_fuzzy=False so downstream consumers can audit every link.
    """
    for stay in stays:
        if stay.match_name_key != candidate.match_name_key:
            continue
        if is_within_stay_window(
            candidate.activity_date,
            stay.arrival_date,
            stay.departure_date,
            tolerance_days,
        ):
            return ExactMatchResult(stay=stay)
    return None
