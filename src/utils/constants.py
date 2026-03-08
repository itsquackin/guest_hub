"""Project-wide constants.

Import from here rather than hard-coding values in individual modules.
"""
from __future__ import annotations

# ── Source system identifiers ─────────────────────────────────────────────────
SOURCE_ROOMS = "rooms"
SOURCE_SPA = "spa"
SOURCE_DINING = "dining"

# ── Name / phone matching separators ─────────────────────────────────────────
NAME_KEY_SEP = "|"
PHONE_KEY_SEP = ":"

# ── Matching thresholds ───────────────────────────────────────────────────────
DEFAULT_DATE_TOLERANCE_DAYS: int = 1
DEFAULT_FUZZY_SCORE_CUTOFF: float = 0.88

# ── Guest roles ───────────────────────────────────────────────────────────────
GUEST_ROLE_PRIMARY = "Primary"
GUEST_ROLE_ACCOMPANYING = "Accompanying"

# ── Match method names ────────────────────────────────────────────────────────
MATCH_EXACT_NAME_DATE = "ExactNameDate"
MATCH_FUZZY_NAME_DATE = "FuzzyNameDate"
MATCH_PHONE_SUPPORT = "PhoneSupport"
MATCH_OUTSIDE_STAY = "OutsideStayWindow"
MATCH_REPEATED_PATTERN = "RepeatedCrossSourcePattern"
MATCH_SAME_LAST_NEAR_STAY = "SameLastNameNearStay"
MATCH_DIFF_LAST_SHARED_PHONE = "DifferentLastNameSharedPhone"

# ── QA issue codes ────────────────────────────────────────────────────────────
QA_INCOMPLETE_NAME = "incomplete_name"
QA_UNPARSEABLE_NAME = "unparseable_name"
QA_MULTI_NAME_FIELD = "multi_name_field"
QA_ODD_DELIMITER = "odd_delimiter"
QA_INHERITED_PHONE = "inherited_phone"
QA_BLANK_PHONE = "blank_phone"
QA_INVALID_PHONE = "invalid_phone"
QA_INCOMPLETE_PHONE = "incomplete_phone"
QA_INTERNATIONAL_PHONE = "international_phone"
QA_SHARED_PHONE = "shared_phone"
QA_UNKNOWN_ROOM_TYPE = "unknown_room_type"
QA_UNKNOWN_ASSIGNED_ROOM_TYPE = "unknown_assigned_room_type"
QA_UNKNOWN_SPECIAL = "unknown_special_request"
QA_DUPLICATE_ROW = "duplicate_row"
QA_UNPARSEABLE_DATE = "unparseable_date"

# ── File glob patterns ────────────────────────────────────────────────────────
ROOM_FILE_GLOB = "*.xml"
SPA_FILE_GLOB = "*.pdf"
DINING_FILE_GLOB = "*.csv"

# ── Reference TSV column names ────────────────────────────────────────────────
ROOM_TYPE_CODE_COL = "room_type_code"
ROOM_TYPE_DESC_COL = "room_type_description"
SPECIAL_CODE_COL = "special_request_code"
SPECIAL_DESC_COL = "special_request_description"

# ── Identity status labels ────────────────────────────────────────────────────
IDENTITY_CONFIRMED = "Confirmed"
IDENTITY_PROBABLE = "Probable"
IDENTITY_QA_REVIEW = "QAReview"
IDENTITY_UNRESOLVED = "Unresolved"
