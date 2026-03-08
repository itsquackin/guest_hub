"""QA candidate generation stubs for ambiguous matching outcomes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PossibleMatchIssue:
    """Represents one reviewable near-match row for QA outputs."""

    source_system: str
    source_activity_key: str
    candidate_guest_id: str
    reason: str
    score: float | None


def build_possible_match_issue(
    source_system: str,
    source_activity_key: str,
    candidate_guest_id: str,
    reason: str,
    score: float | None = None,
) -> PossibleMatchIssue:
    """Create a standardized `qa_possible_matches` issue row."""
    return PossibleMatchIssue(
        source_system=source_system,
        source_activity_key=source_activity_key,
        candidate_guest_id=candidate_guest_id,
        reason=reason,
        score=score,
    )
