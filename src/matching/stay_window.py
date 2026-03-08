"""Stay-window date logic.

Canonical location for the arrival/departure ± tolerance rule.
exact_match.py and fuzzy_match.py both import from here.
"""
from __future__ import annotations

from datetime import date, timedelta

from src.utils.constants import DEFAULT_DATE_TOLERANCE_DAYS


def is_within_stay_window(
    activity_date: date,
    arrival_date: date,
    departure_date: date,
    tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
) -> bool:
    """Return True when *activity_date* falls within the stay window.

    The window is ``arrival - tolerance`` through ``departure + tolerance``
    (inclusive on both ends).  Default tolerance is ±1 day per spec.
    """
    window_start = arrival_date - timedelta(days=tolerance_days)
    window_end = departure_date + timedelta(days=tolerance_days)
    return window_start <= activity_date <= window_end


def days_from_stay(
    activity_date: date,
    arrival_date: date,
    departure_date: date,
) -> int:
    """Return the number of days the activity falls outside the raw stay.

    Returns 0 when the date is within the stay (inclusive), positive when
    after checkout, negative when before arrival.
    """
    if activity_date < arrival_date:
        return (activity_date - arrival_date).days  # negative
    if activity_date > departure_date:
        return (activity_date - departure_date).days  # positive
    return 0
