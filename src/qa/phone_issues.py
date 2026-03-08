"""QA checks for phone number quality.

Detects blank, incomplete, international-like, inherited, and shared phones.
"""
from __future__ import annotations

import logging
from collections import Counter

from src.cleaners.phones import (
    is_blank_phone,
    is_incomplete_like,
    is_international_like,
    is_valid_like,
)
from src.models.canonical_schema import DiningCanonicalRow, RoomsCanonicalRow
from src.models.qa_schema import QaPhoneIssue
from src.utils.constants import (
    QA_BLANK_PHONE,
    QA_INCOMPLETE_PHONE,
    QA_INHERITED_PHONE,
    QA_INTERNATIONAL_PHONE,
    QA_SHARED_PHONE,
)

logger = logging.getLogger(__name__)


def check_phone_quality(
    row: RoomsCanonicalRow | DiningCanonicalRow,
    *,
    shared_phone_keys: set[str] | None = None,
) -> list[QaPhoneIssue]:
    """Return QaPhoneIssue records for any phone problems in *row*."""
    issues: list[QaPhoneIssue] = []
    source_system = getattr(row, "source_system", "")
    source_row_id = getattr(row, "source_row_id", "")
    conf_num = getattr(row, "confirmation_number", None)
    phone_raw = getattr(row, "phone_raw", None)
    phone_clean = getattr(row, "phone_clean", None)
    is_inherited = getattr(row, "phone_is_inherited", False)
    is_shared = getattr(row, "phone_is_shared", False)

    def _issue(code: str, detail: str | None = None) -> QaPhoneIssue:
        return QaPhoneIssue(
            source_system=source_system,
            source_row_id=source_row_id,
            confirmation_number=conf_num,
            phone_raw=phone_raw,
            phone_clean=phone_clean,
            issue_code=code,
            issue_detail=detail,
            is_inherited=is_inherited,
            is_shared=is_shared,
        )

    if is_blank_phone(phone_raw):
        issues.append(_issue(QA_BLANK_PHONE))
        return issues

    if is_incomplete_like(phone_clean):
        issues.append(_issue(QA_INCOMPLETE_PHONE, f"digits:{len(phone_clean or '')}"))
    elif is_international_like(phone_clean, phone_raw):
        issues.append(_issue(QA_INTERNATIONAL_PHONE, f"raw:{phone_raw!r}"))

    if is_inherited:
        issues.append(_issue(QA_INHERITED_PHONE))

    match_phone_key = getattr(row, "match_phone_key", None)
    if shared_phone_keys and match_phone_key in shared_phone_keys:
        issues.append(_issue(QA_SHARED_PHONE, f"key:{match_phone_key}"))

    return issues


def find_shared_phone_keys(
    rows: list[RoomsCanonicalRow | DiningCanonicalRow],
    threshold: int = 3,
) -> set[str]:
    """Return phone keys shared by more than *threshold* rows."""
    counts: Counter[str] = Counter()
    for row in rows:
        key = getattr(row, "match_phone_key", None)
        if key:
            counts[key] += 1
    return {k for k, n in counts.items() if n > threshold}


def check_rooms_phone_issues(
    rows: list[RoomsCanonicalRow],
    *,
    threshold: int = 3,
) -> list[QaPhoneIssue]:
    """Run phone QA across all rooms canonical rows."""
    shared = find_shared_phone_keys(rows, threshold=threshold)  # type: ignore[arg-type]
    issues: list[QaPhoneIssue] = []
    for row in rows:
        issues.extend(check_phone_quality(row, shared_phone_keys=shared))
    logger.info("Found %d room phone issues", len(issues))
    return issues


def check_dining_phone_issues(
    rows: list[DiningCanonicalRow],
    *,
    threshold: int = 3,
) -> list[QaPhoneIssue]:
    """Run phone QA across all dining canonical rows."""
    shared = find_shared_phone_keys(rows, threshold=threshold)  # type: ignore[arg-type]
    issues: list[QaPhoneIssue] = []
    for row in rows:
        issues.extend(check_phone_quality(row, shared_phone_keys=shared))
    logger.info("Found %d dining phone issues", len(issues))
    return issues
