"""Dataclasses for hub-level output tables.

Hub tables are the reporting-grade, cross-source outputs produced after
matching.  They separate guest identity truth from stay/activity facts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── Guest dimension ──────────────────────────────────────────────────────────

@dataclass
class DimGuest:
    """One row per resolved person identity across all source systems."""
    guest_id: str = ""
    best_first_name: Optional[str] = None
    best_last_name: Optional[str] = None
    best_full_name: Optional[str] = None
    canonical_name_key: Optional[str] = None
    first_seen_date: Optional[date] = None
    last_seen_date: Optional[date] = None

    # Source system presence flags
    has_room_activity: bool = False
    has_spa_activity: bool = False
    has_dining_activity: bool = False

    # Activity counts
    room_activity_count: int = 0
    spa_activity_count: int = 0
    dining_activity_count: int = 0
    linked_phone_count: int = 0

    # Confidence
    name_confidence: Optional[str] = None   # "high", "medium", "low"
    identity_status: str = "Unresolved"     # see IdentityStatus enum


# ── Phone dimension ──────────────────────────────────────────────────────────

@dataclass
class DimPhone:
    """One row per normalized phone number."""
    phone_id: str = ""
    phone_clean: Optional[str] = None
    phone_raw_example: Optional[str] = None
    linked_guest_count: int = 0
    is_shared_phone: bool = False
    is_international_like: bool = False
    is_incomplete_like: bool = False
    is_valid_like: bool = False


# ── Room stay fact ────────────────────────────────────────────────────────────

@dataclass
class FactRoomStay:
    """One row per reservation/stay — the financial source of truth for rooms.

    This table holds rate and night counts exactly once, regardless of how
    many guests are linked to the reservation via ``BridgeGuestRoomStay``.
    """
    confirmation_number: str = ""
    arrival_date: Optional[date] = None
    departure_date: Optional[date] = None
    nights: Optional[int] = None
    rate_code: Optional[str] = None
    nightly_rate: Optional[float] = None
    room_type_code: Optional[str] = None
    room_type_description: Optional[str] = None
    assigned_room_type_code: Optional[str] = None
    assigned_room_type_description: Optional[str] = None
    company_raw: Optional[str] = None
    reservation_status_raw: Optional[str] = None
    specials_raw: Optional[str] = None
    vip_status_raw: Optional[str] = None
    last_stay_date: Optional[date] = None
    last_room_raw: Optional[str] = None


# ── Guest–room stay bridge ────────────────────────────────────────────────────

@dataclass
class BridgeGuestRoomStay:
    """Links a resolved guest to a room stay.

    Multiple rows may exist per stay (one per guest attached to the
    reservation) but the stay financials live only in ``FactRoomStay``.
    """
    guest_id: str = ""
    confirmation_number: str = ""
    reservation_guest_key: Optional[str] = None
    guest_role: str = "Primary"
    is_primary_reservation_guest: bool = True
    phone_is_inherited: bool = False
    link_source: str = "rooms_canonical"


# ── Guest–activity bridge ─────────────────────────────────────────────────────

@dataclass
class BridgeGuestActivity:
    """One row per guest-to-activity link across all source systems."""
    guest_id: str = ""
    source_system: str = ""
    source_activity_key: str = ""
    activity_date: Optional[date] = None
    activity_time: Optional[str] = None
    match_method: str = ""
    match_score: Optional[float] = None
    match_flag_fuzzy: bool = False
    matched_within_stay_window: bool = False
    matched_by_phone_support: bool = False
    outside_stay_window_flag: bool = False
    repeated_pattern_flag: bool = False
    qa_review_required: bool = False
    linked_phones: list[str] = field(default_factory=list)
