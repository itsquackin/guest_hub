"""Fuzzy name/date matching stubs."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from src.matching.exact_match import ExactMatchCandidate, RoomStayContext, is_within_stay_window


@dataclass(slots=True)
class FuzzyMatchResult:
    """Represents a fuzzy match candidate with explainability fields."""

    stay: RoomStayContext
    score: float
    method: str = "FuzzyNameDate"
    match_flag_fuzzy: bool = True


def fuzzy_name_score(left: str, right: str) -> float:
    """Compute a simple fuzzy similarity score in [0, 1]."""
    return SequenceMatcher(None, left, right).ratio()


def match_fuzzy_name_date(
    candidate: ExactMatchCandidate,
    stays: list[RoomStayContext],
    score_cutoff: float = 0.88,
    tolerance_days: int = 1,
) -> FuzzyMatchResult | None:
    """Find best fuzzy name/date match within configured threshold.

    TODO: replace SequenceMatcher with production-grade configurable matcher.
    """
    best: FuzzyMatchResult | None = None
    for stay in stays:
        if not is_within_stay_window(candidate.activity_date, stay.arrival_date, stay.departure_date, tolerance_days):
            continue
        score = fuzzy_name_score(candidate.match_name_key, stay.match_name_key)
        if score < score_cutoff:
            continue
        if best is None or score > best.score:
            best = FuzzyMatchResult(stay=stay, score=score)
    return best
