"""Fuzzy name/date matching.

Links activity records where names are close but not identical.
Fuzzy matches are always visibly flagged (match_flag_fuzzy=True).

Uses rapidfuzz for production-grade string similarity when available;
falls back to stdlib SequenceMatcher.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.matching.exact_match import ExactMatchCandidate, RoomStayContext
from src.matching.stay_window import is_within_stay_window
from src.utils.constants import DEFAULT_DATE_TOLERANCE_DAYS, DEFAULT_FUZZY_SCORE_CUTOFF, MATCH_FUZZY_NAME_DATE

# ── Fuzzy scorer (rapidfuzz preferred) ───────────────────────────────────────

try:
    from rapidfuzz.distance import JaroWinkler
    def _fuzzy_score(a: str, b: str) -> float:
        """JaroWinkler similarity in [0, 1] via rapidfuzz."""
        return JaroWinkler.normalized_similarity(a, b)
    _SCORER_NAME = "JaroWinkler/rapidfuzz"
except ImportError:
    from difflib import SequenceMatcher
    def _fuzzy_score(a: str, b: str) -> float:
        """SequenceMatcher ratio fallback."""
        return SequenceMatcher(None, a, b).ratio()
    _SCORER_NAME = "SequenceMatcher/stdlib"


@dataclass(slots=True)
class FuzzyMatchResult:
    """A fuzzy name/date match candidate with full explainability payload."""
    stay: RoomStayContext
    score: float
    method: str = MATCH_FUZZY_NAME_DATE
    match_flag_fuzzy: bool = True          # always True — must be visibly flagged
    matched_within_stay_window: bool = True


def fuzzy_name_score(left: str, right: str) -> float:
    """Compute a string similarity score in [0, 1].

    Uses JaroWinkler (via rapidfuzz) when available, SequenceMatcher otherwise.
    """
    if not left or not right:
        return 0.0
    return _fuzzy_score(left, right)


def match_fuzzy_name_date(
    candidate: ExactMatchCandidate,
    stays: list[RoomStayContext],
    score_cutoff: float = DEFAULT_FUZZY_SCORE_CUTOFF,
    tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
) -> FuzzyMatchResult | None:
    """Find the best fuzzy name match within the date window.

    Returns the highest-scoring stay above *score_cutoff* whose window
    contains the activity date.  Returns None when nothing qualifies.

    The result always has match_flag_fuzzy=True so downstream tables
    clearly surface it for review.
    """
    best: FuzzyMatchResult | None = None
    for stay in stays:
        if not is_within_stay_window(
            candidate.activity_date,
            stay.arrival_date,
            stay.departure_date,
            tolerance_days,
        ):
            continue
        score = fuzzy_name_score(candidate.match_name_key, stay.match_name_key)
        if score < score_cutoff:
            continue
        if best is None or score > best.score:
            best = FuzzyMatchResult(stay=stay, score=score)
    return best


def are_fuzzy_scores_ambiguous(
    candidate: ExactMatchCandidate,
    stays: list[RoomStayContext],
    score_cutoff: float = DEFAULT_FUZZY_SCORE_CUTOFF,
    tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
    ambiguity_margin: float = 0.03,
) -> list[FuzzyMatchResult]:
    """Return all qualifying fuzzy matches when top scores are too close.

    When the best and second-best score differ by less than *ambiguity_margin*,
    both (and any ties) are returned so they can be routed to QA instead of
    force-joined.
    """
    candidates: list[FuzzyMatchResult] = []
    for stay in stays:
        if not is_within_stay_window(
            candidate.activity_date,
            stay.arrival_date,
            stay.departure_date,
            tolerance_days,
        ):
            continue
        score = fuzzy_name_score(candidate.match_name_key, stay.match_name_key)
        if score >= score_cutoff:
            candidates.append(FuzzyMatchResult(stay=stay, score=score))

    if len(candidates) <= 1:
        return candidates

    candidates.sort(key=lambda r: r.score, reverse=True)
    best_score = candidates[0].score
    ambiguous = [r for r in candidates if best_score - r.score <= ambiguity_margin]
    return ambiguous if len(ambiguous) > 1 else [candidates[0]]
