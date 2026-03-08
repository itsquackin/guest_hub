"""QA checks for guest name quality.

Detects incomplete names, unparseable segments, and fields that appear
to contain multiple people's names.
"""
from __future__ import annotations

import logging

from src.cleaners.names import classify_name_quality, has_multiple_names_in_field
from src.models.canonical_schema import DiningCanonicalRow, RoomsCanonicalRow, SpaCanonicalRow
from src.models.qa_schema import QaNameIssue
from src.utils.constants import (
    QA_INCOMPLETE_NAME,
    QA_MULTI_NAME_FIELD,
    QA_ODD_DELIMITER,
)

logger = logging.getLogger(__name__)

AnyCanonicalRow = RoomsCanonicalRow | SpaCanonicalRow | DiningCanonicalRow


def check_name_quality(row: AnyCanonicalRow) -> list[QaNameIssue]:
    """Return QaNameIssue records for any name-quality problems in *row*."""
    issues: list[QaNameIssue] = []
    source_system = getattr(row, "source_system", "")
    source_row_id = getattr(row, "source_row_id", "")
    conf_num = getattr(row, "confirmation_number", None)
    name_raw = getattr(row, "guest_name_raw", None)
    first = getattr(row, "first_name", None)
    last = getattr(row, "last_name", None)

    quality = classify_name_quality(first, last)
    if quality in ("both_blank", "last_only", "first_only"):
        issues.append(
            QaNameIssue(
                source_system=source_system,
                source_row_id=source_row_id,
                confirmation_number=conf_num,
                guest_name_raw=name_raw,
                issue_code=QA_INCOMPLETE_NAME,
                issue_detail=f"quality:{quality}:{name_raw!r}",
            )
        )

    # Check for multi-name contamination in the primary name field
    if name_raw and has_multiple_names_in_field(name_raw):
        issues.append(
            QaNameIssue(
                source_system=source_system,
                source_row_id=source_row_id,
                confirmation_number=conf_num,
                guest_name_raw=name_raw,
                issue_code=QA_MULTI_NAME_FIELD,
                issue_detail=f"multi_name:{name_raw!r}",
            )
        )

    return issues


def check_rooms_name_issues(rows: list[RoomsCanonicalRow]) -> list[QaNameIssue]:
    """Run name-quality checks across all rooms canonical rows."""
    issues: list[QaNameIssue] = []
    for row in rows:
        issues.extend(check_name_quality(row))
    logger.info("Found %d room name issues", len(issues))
    return issues


def check_spa_name_issues(rows: list[SpaCanonicalRow]) -> list[QaNameIssue]:
    """Run name-quality checks across all spa canonical rows."""
    issues: list[QaNameIssue] = []
    for row in rows:
        issues.extend(check_name_quality(row))
    logger.info("Found %d spa name issues", len(issues))
    return issues


def check_dining_name_issues(rows: list[DiningCanonicalRow]) -> list[QaNameIssue]:
    """Run name-quality checks across all dining canonical rows."""
    issues: list[QaNameIssue] = []
    for row in rows:
        issues.extend(check_name_quality(row))
    logger.info("Found %d dining name issues", len(issues))
    return issues
