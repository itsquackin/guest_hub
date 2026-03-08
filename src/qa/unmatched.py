"""Unmatched record collection.

Gathers spa and dining rows that could not be confidently linked to any
room guest, and emits them as QaUnmatchedRecord rows for review.
"""
from __future__ import annotations

import logging

from src.models.canonical_schema import DiningCanonicalRow, SpaCanonicalRow
from src.models.qa_schema import QaUnmatchedRecord

logger = logging.getLogger(__name__)


def collect_unmatched_spa(
    spa_rows: list[SpaCanonicalRow],
    matched_keys: set[str],
) -> list[QaUnmatchedRecord]:
    """Return QaUnmatchedRecord rows for spa appointments not in *matched_keys*.

    Args:
        spa_rows: All spa canonical rows for a run.
        matched_keys: Set of source_row_id values that were successfully linked.
    """
    unmatched: list[QaUnmatchedRecord] = []
    for row in spa_rows:
        if row.source_row_id not in matched_keys:
            unmatched.append(
                QaUnmatchedRecord(
                    source_system=row.source_system,
                    source_row_id=row.source_row_id,
                    guest_name_raw=row.guest_name_raw,
                    match_name_key=row.match_name_key,
                    activity_date=row.activity_date,
                    reason="no_confident_match",
                )
            )
    logger.info("Unmatched spa appointments: %d", len(unmatched))
    return unmatched


def collect_unmatched_dining(
    dining_rows: list[DiningCanonicalRow],
    matched_keys: set[str],
) -> list[QaUnmatchedRecord]:
    """Return QaUnmatchedRecord rows for dining visits not in *matched_keys*."""
    unmatched: list[QaUnmatchedRecord] = []
    for row in dining_rows:
        if row.source_row_id not in matched_keys:
            unmatched.append(
                QaUnmatchedRecord(
                    source_system=row.source_system,
                    source_row_id=row.source_row_id,
                    guest_name_raw=row.guest_name_raw,
                    match_name_key=row.match_name_key,
                    activity_date=row.activity_date,
                    reason="no_confident_match",
                )
            )
    logger.info("Unmatched dining visits: %d", len(unmatched))
    return unmatched
