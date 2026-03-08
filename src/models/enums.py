"""Project-wide enumerations."""
from __future__ import annotations

from enum import Enum


class GuestRole(str, Enum):
    """Whether a guest is the primary reservation holder or an accompanying guest."""
    PRIMARY = "Primary"
    ACCOMPANYING = "Accompanying"


class MatchMethod(str, Enum):
    """Named match methods used to link guest activity across source systems."""
    EXACT_NAME_DATE = "ExactNameDate"
    FUZZY_NAME_DATE = "FuzzyNameDate"
    PHONE_SUPPORT = "PhoneSupport"
    OUTSIDE_STAY_WINDOW = "OutsideStayWindow"
    REPEATED_CROSS_SOURCE = "RepeatedCrossSourcePattern"
    SAME_LAST_NEAR_STAY = "SameLastNameNearStay"
    DIFF_LAST_SHARED_PHONE = "DifferentLastNameSharedPhone"


class IdentityStatus(str, Enum):
    """Confidence level for a resolved guest identity."""
    CONFIRMED = "Confirmed"
    PROBABLE = "Probable"
    QA_REVIEW = "QAReview"
    UNRESOLVED = "Unresolved"


class PhoneType(str, Enum):
    """Classification of a phone record."""
    VALID = "Valid"
    INHERITED = "Inherited"
    SHARED = "Shared"
    INVALID = "Invalid"
    INTERNATIONAL_LIKE = "InternationalLike"
    INCOMPLETE = "Incomplete"
    BLANK = "Blank"


class QAIssueType(str, Enum):
    """Standardized QA issue codes surfaced by validation checks."""
    INCOMPLETE_NAME = "incomplete_name"
    UNPARSEABLE_NAME = "unparseable_name"
    MULTI_NAME_FIELD = "multi_name_field"
    ODD_DELIMITER = "odd_delimiter"
    INHERITED_PHONE = "inherited_phone"
    BLANK_PHONE = "blank_phone"
    INVALID_PHONE = "invalid_phone"
    INCOMPLETE_PHONE = "incomplete_phone"
    INTERNATIONAL_PHONE = "international_phone"
    SHARED_PHONE = "shared_phone"
    UNKNOWN_ROOM_TYPE = "unknown_room_type"
    UNKNOWN_ASSIGNED_ROOM_TYPE = "unknown_assigned_room_type"
    UNKNOWN_SPECIAL = "unknown_special_request"
    DUPLICATE_ROW = "duplicate_row"
    UNPARSEABLE_DATE = "unparseable_date"
