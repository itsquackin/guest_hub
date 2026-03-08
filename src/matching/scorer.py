"""Match scoring: composite result record and confidence helpers.

Scoring priority (highest to lowest):
1. ExactNameDate (score = 1.0, no fuzzy flag)
2. FuzzyNameDate (score = fuzzy similarity, fuzzy flag set)
3. Supporting signals add context but don't change the primary method.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from src.utils.constants import (
    MATCH_EXACT_NAME_DATE,
    MATCH_FUZZY_NAME_DATE,
    MATCH_PHONE_SUPPORT,
)


@dataclass
class MatchResult:
    """Full explainability record for one guest-to-activity link."""
    guest_id: str
    source_system: str
    source_activity_key: str
    activity_date: date | None
    activity_time: str | None
    match_method: str
    match_score: float
    match_flag_fuzzy: bool
    matched_within_stay_window: bool = True
    matched_by_phone_support: bool = False
    outside_stay_window_flag: bool = False
    repeated_pattern_flag: bool = False
    qa_review_required: bool = False
    supporting_signals: list[str] = field(default_factory=list)


def make_exact_result(
    guest_id: str,
    source_system: str,
    source_activity_key: str,
    activity_date: date | None,
    activity_time: str | None = None,
) -> MatchResult:
    """Build a MatchResult for an ExactNameDate link."""
    return MatchResult(
        guest_id=guest_id,
        source_system=source_system,
        source_activity_key=source_activity_key,
        activity_date=activity_date,
        activity_time=activity_time,
        match_method=MATCH_EXACT_NAME_DATE,
        match_score=1.0,
        match_flag_fuzzy=False,
        matched_within_stay_window=True,
    )


def make_fuzzy_result(
    guest_id: str,
    source_system: str,
    source_activity_key: str,
    activity_date: date | None,
    score: float,
    activity_time: str | None = None,
    *,
    qa_review: bool = False,
) -> MatchResult:
    """Build a MatchResult for a FuzzyNameDate link.

    Fuzzy results always have match_flag_fuzzy=True.
    qa_review=True marks ambiguous matches that need human review.
    """
    return MatchResult(
        guest_id=guest_id,
        source_system=source_system,
        source_activity_key=source_activity_key,
        activity_date=activity_date,
        activity_time=activity_time,
        match_method=MATCH_FUZZY_NAME_DATE,
        match_score=score,
        match_flag_fuzzy=True,
        matched_within_stay_window=True,
        qa_review_required=qa_review,
    )


def add_phone_support(result: MatchResult) -> MatchResult:
    """Mark a MatchResult as having phone-support confirmation."""
    result.matched_by_phone_support = True
    result.supporting_signals.append(MATCH_PHONE_SUPPORT)
    return result


def confidence_label(result: MatchResult) -> str:
    """Return a human-readable confidence label for a match result.

    Returns one of: ``"high"``, ``"medium"``, ``"low"``.
    """
    if result.match_method == MATCH_EXACT_NAME_DATE:
        return "high"
    if result.match_flag_fuzzy and result.match_score >= 0.92:
        return "medium"
    return "low"
