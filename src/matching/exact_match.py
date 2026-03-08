"""Exact name/date matching stubs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(slots=True)
class ExactMatchCandidate:
    """Activity candidate for exact matching against room guest rows."""

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


def is_within_stay_window(activity_date: date, arrival_date: date, departure_date: date, tolerance_days: int = 1) -> bool:
    """Return whether date is within arrival/departure with ± tolerance."""
    return (arrival_date - timedelta(days=tolerance_days)) <= activity_date <= (
        departure_date + timedelta(days=tolerance_days)
    )


def match_exact_name_date(
    candidate: ExactMatchCandidate,
    stays: list[RoomStayContext],
    tolerance_days: int = 1,
) -> RoomStayContext | None:
    """Find an exact name + date-window match.

    TODO: expand to return explainability payload (method, score, flags).
    """
    for stay in stays:
        if stay.match_name_key != candidate.match_name_key:
            continue
        if is_within_stay_window(candidate.activity_date, stay.arrival_date, stay.departure_date, tolerance_days):
            return stay
    return None
