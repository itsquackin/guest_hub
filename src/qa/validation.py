"""Orchestration layer for QA validation across canonical tables.

Calls individual check modules and assembles a unified QA issue list.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.models.canonical_schema import (
    DiningCanonicalRow,
    RoomsCanonicalRow,
    SpaCanonicalRow,
)
from src.models.qa_schema import QaLookupIssue, QaNameIssue, QaPhoneIssue
from src.qa.duplicate_checks import find_duplicate_reservation_guests
from src.qa.name_issues import (
    check_dining_name_issues,
    check_rooms_name_issues,
    check_spa_name_issues,
)
from src.qa.phone_issues import check_dining_phone_issues, check_rooms_phone_issues

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Aggregated QA output for one pipeline run."""
    name_issues: list[QaNameIssue] = field(default_factory=list)
    phone_issues: list[QaPhoneIssue] = field(default_factory=list)
    lookup_issues: list[QaLookupIssue] = field(default_factory=list)
    duplicate_issues: list[QaNameIssue] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return (
            len(self.name_issues)
            + len(self.phone_issues)
            + len(self.lookup_issues)
            + len(self.duplicate_issues)
        )


def validate_canonical_outputs(
    rooms_rows: list[RoomsCanonicalRow],
    spa_rows: list[SpaCanonicalRow],
    dining_rows: list[DiningCanonicalRow],
    lookup_issues: list[QaLookupIssue] | None = None,
    shared_phone_threshold: int = 3,
) -> ValidationReport:
    """Run all QA checks and return a ValidationReport.

    Args:
        rooms_rows: Expanded guest-grain rooms canonical rows.
        spa_rows: Spa canonical rows.
        dining_rows: Dining canonical rows.
        lookup_issues: Pre-collected lookup QA issues from rooms_enrich.
    """
    report = ValidationReport()

    # Name checks
    report.name_issues.extend(check_rooms_name_issues(rooms_rows))
    report.name_issues.extend(check_spa_name_issues(spa_rows))
    report.name_issues.extend(check_dining_name_issues(dining_rows))

    # Phone checks
    report.phone_issues.extend(
        check_rooms_phone_issues(rooms_rows, threshold=shared_phone_threshold)
    )
    report.phone_issues.extend(
        check_dining_phone_issues(dining_rows, threshold=shared_phone_threshold)
    )

    # Lookup issues (passed in from enrichment step)
    if lookup_issues:
        report.lookup_issues.extend(lookup_issues)

    # Duplicate checks
    report.duplicate_issues.extend(find_duplicate_reservation_guests(rooms_rows))

    logger.info(
        "Validation complete: %d name, %d phone, %d lookup, %d duplicate issues",
        len(report.name_issues),
        len(report.phone_issues),
        len(report.lookup_issues),
        len(report.duplicate_issues),
    )
    return report
