"""Duplicate detection checks for canonical source tables."""
from __future__ import annotations

import logging
from collections import Counter

from src.models.canonical_schema import RoomsCanonicalRow
from src.models.qa_schema import QaNameIssue
from src.utils.constants import QA_DUPLICATE_ROW

logger = logging.getLogger(__name__)


def find_duplicate_reservation_guests(
    rows: list[RoomsCanonicalRow],
) -> list[QaNameIssue]:
    """Detect rows sharing the same confirmation_number + guest_sequence.

    Returns QaNameIssue records for any duplicates found.
    """
    counts: Counter[str] = Counter()
    for row in rows:
        key = f"{row.confirmation_number}#{row.guest_sequence_in_reservation}"
        counts[key] += 1

    issues: list[QaNameIssue] = []
    for row in rows:
        key = f"{row.confirmation_number}#{row.guest_sequence_in_reservation}"
        if counts[key] > 1:
            issues.append(
                QaNameIssue(
                    source_system=row.source_system,
                    source_row_id=row.source_row_id,
                    confirmation_number=row.confirmation_number,
                    guest_name_raw=row.guest_name_raw,
                    issue_code=QA_DUPLICATE_ROW,
                    issue_detail=f"dup_key:{key}",
                )
            )

    logger.info("Found %d duplicate reservation-guest rows", len(issues))
    return issues
