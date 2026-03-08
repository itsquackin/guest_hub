"""Dataclasses for QA and exception output tables.

QA outputs surface ambiguity and data-quality issues instead of forcing
uncertain joins or silently dropping bad data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class QaNameIssue:
    """One row per name-quality problem detected in any canonical source."""
    source_system: str = ""
    source_row_id: str = ""
    confirmation_number: Optional[str] = None
    guest_name_raw: Optional[str] = None
    issue_code: str = ""
    issue_detail: Optional[str] = None


@dataclass
class QaPhoneIssue:
    """One row per phone-quality problem detected in any canonical source."""
    source_system: str = ""
    source_row_id: str = ""
    confirmation_number: Optional[str] = None
    phone_raw: Optional[str] = None
    phone_clean: Optional[str] = None
    issue_code: str = ""
    issue_detail: Optional[str] = None
    is_inherited: bool = False
    is_shared: bool = False


@dataclass
class QaLookupIssue:
    """One row per unknown room-type or special-request code."""
    source_system: str = ""
    source_row_id: str = ""
    confirmation_number: Optional[str] = None
    lookup_type: str = ""      # "room_type", "assigned_room_type", "special_request"
    lookup_code: Optional[str] = None
    issue_code: str = ""


@dataclass
class QaPossibleMatch:
    """One row per near-match that requires human review.

    These are candidates that did not meet the threshold for automatic
    linking and must not be forced into the hub tables.
    """
    source_system: str = ""
    source_activity_key: str = ""
    candidate_guest_id: str = ""
    activity_date: Optional[date] = None
    match_method: str = ""
    match_score: Optional[float] = None
    reason: str = ""
    left_name_key: Optional[str] = None
    right_name_key: Optional[str] = None
    left_phone_key: Optional[str] = None
    right_phone_key: Optional[str] = None


@dataclass
class QaUnmatchedRecord:
    """One row per spa or dining record not confidently linked to a guest."""
    source_system: str = ""
    source_row_id: str = ""
    guest_name_raw: Optional[str] = None
    match_name_key: Optional[str] = None
    activity_date: Optional[date] = None
    reason: str = "no_confident_match"


@dataclass
class QaRunSummary:
    """Counts by pipeline stage for one run."""
    run_id: str = ""
    run_timestamp: str = ""

    # Load counts
    rooms_files_loaded: int = 0
    spa_files_loaded: int = 0
    dining_files_loaded: int = 0

    # Parse counts
    rooms_raw_records: int = 0
    spa_raw_records: int = 0
    dining_raw_records: int = 0

    # Canonical counts
    rooms_canonical_rows: int = 0
    spa_canonical_rows: int = 0
    dining_canonical_rows: int = 0

    # Expansion
    rooms_primary_guests: int = 0
    rooms_accompanying_guests: int = 0

    # QA issues
    name_issues: int = 0
    phone_issues: int = 0
    lookup_issues: int = 0

    # Matching
    exact_matches: int = 0
    fuzzy_matches: int = 0
    phone_supported_matches: int = 0
    possible_matches_flagged: int = 0
    unmatched_spa: int = 0
    unmatched_dining: int = 0

    # Hub outputs
    dim_guest_rows: int = 0
    dim_phone_rows: int = 0
    fact_room_stay_rows: int = 0
    bridge_guest_activity_rows: int = 0

    # Errors
    parse_errors: list[str] = field(default_factory=list)
