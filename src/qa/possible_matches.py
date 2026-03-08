"""QA output generation for near-matches that need human review.

Uncertain joins become QA rows here instead of being force-linked.
"""
from __future__ import annotations

import logging
from datetime import date

from src.models.qa_schema import QaPossibleMatch

logger = logging.getLogger(__name__)


def build_possible_match_issue(
    source_system: str,
    source_activity_key: str,
    candidate_guest_id: str,
    reason: str,
    score: float | None = None,
    *,
    activity_date: date | None = None,
    match_method: str = "",
    left_name_key: str | None = None,
    right_name_key: str | None = None,
    left_phone_key: str | None = None,
    right_phone_key: str | None = None,
) -> QaPossibleMatch:
    """Create a standardized ``qa_possible_matches`` issue row."""
    return QaPossibleMatch(
        source_system=source_system,
        source_activity_key=source_activity_key,
        candidate_guest_id=candidate_guest_id,
        activity_date=activity_date,
        match_method=match_method,
        match_score=score,
        reason=reason,
        left_name_key=left_name_key,
        right_name_key=right_name_key,
        left_phone_key=left_phone_key,
        right_phone_key=right_phone_key,
    )


def collect_ambiguous_fuzzy(
    source_system: str,
    source_activity_key: str,
    candidates: list,  # list[FuzzyMatchResult]
    activity_date: date | None = None,
    left_name_key: str | None = None,
) -> list[QaPossibleMatch]:
    """Build QaPossibleMatch rows for ambiguous fuzzy match candidates.

    Called when multiple fuzzy candidates score within the ambiguity margin
    — all candidates are surfaced for review rather than arbitrarily picking one.
    """
    issues: list[QaPossibleMatch] = []
    for result in candidates:
        issues.append(
            build_possible_match_issue(
                source_system=source_system,
                source_activity_key=source_activity_key,
                candidate_guest_id=result.stay.guest_id,
                reason="fuzzy_only",
                score=result.score,
                activity_date=activity_date,
                match_method=result.method,
                left_name_key=left_name_key,
                right_name_key=result.stay.match_name_key,
            )
        )
    return issues


def collect_outside_stay_window(
    source_system: str,
    source_activity_key: str,
    guest_id: str,
    score: float | None,
    activity_date: date | None = None,
    left_name_key: str | None = None,
    right_name_key: str | None = None,
) -> QaPossibleMatch:
    """Create a QA row for same-name activity outside the stay window."""
    return build_possible_match_issue(
        source_system=source_system,
        source_activity_key=source_activity_key,
        candidate_guest_id=guest_id,
        reason="same_name_outside_stay_window",
        score=score,
        activity_date=activity_date,
        left_name_key=left_name_key,
        right_name_key=right_name_key,
    )


def collect_shared_phone_different_name(
    source_system: str,
    source_activity_key: str,
    guest_id: str,
    activity_date: date | None = None,
    left_name_key: str | None = None,
    right_name_key: str | None = None,
    phone_key: str | None = None,
) -> QaPossibleMatch:
    """Create a QA row for shared-phone / different-last-name candidates."""
    return build_possible_match_issue(
        source_system=source_system,
        source_activity_key=source_activity_key,
        candidate_guest_id=guest_id,
        reason="same_phone_different_last_name",
        score=None,
        activity_date=activity_date,
        left_name_key=left_name_key,
        right_name_key=right_name_key,
        left_phone_key=phone_key,
        right_phone_key=phone_key,
    )
