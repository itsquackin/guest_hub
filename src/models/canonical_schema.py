"""Dataclasses for canonical source-system output rows.

Each canonical table is guest- or activity-grain and is produced by the
transform layer before any cross-source matching takes place.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── Rooms canonical ──────────────────────────────────────────────────────────

@dataclass
class RoomsCanonicalRow:
    """One row per individual guest attached to a room reservation/stay.

    Primary guests and every accompanying guest each get their own row.
    Financial fields (nightly_rate, nights) are kept here for reference but
    the authoritative stay-level fact is ``FactRoomStay``.
    """
    # Provenance
    source_system: str = ""
    source_file_name: str = ""
    source_row_id: str = ""
    load_timestamp: str = ""

    # Booking metadata
    booked_by_raw: Optional[str] = None
    booked_on_date: Optional[date] = None
    confirmation_number: str = ""

    # Guest name (raw + cleaned)
    guest_name_raw: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name_clean: Optional[str] = None
    match_name_key: Optional[str] = None

    # Reservation guest linkage
    primary_guest_name_raw: Optional[str] = None
    accompanying_guest_raw: Optional[str] = None
    guest_role: str = "Primary"
    guest_sequence_in_reservation: int = 1
    is_primary_reservation_guest: bool = True
    is_expanded_from_accompanying_text: bool = False
    relationship_to_primary_guest: Optional[str] = None

    # Stay dates
    arrival_date: Optional[date] = None
    departure_date: Optional[date] = None
    nights: Optional[int] = None
    stay_window_start: Optional[date] = None
    stay_window_end: Optional[date] = None

    # Rate / room
    rate_code: Optional[str] = None
    nightly_rate: Optional[float] = None
    room_type_code: Optional[str] = None
    room_type_description: Optional[str] = None
    assigned_room_type_code: Optional[str] = None
    assigned_room_type_description: Optional[str] = None

    # Reservation details
    company_raw: Optional[str] = None
    reservation_status_raw: Optional[str] = None
    specials_raw: Optional[str] = None
    specials_list: list[str] = field(default_factory=list)
    specials_descriptions: list[str] = field(default_factory=list)
    last_stay_date: Optional[date] = None
    last_room_raw: Optional[str] = None
    vip_status_raw: Optional[str] = None

    # Phone
    phone_raw: Optional[str] = None
    phone_clean: Optional[str] = None
    match_phone_key: Optional[str] = None
    phone_is_inherited: bool = False
    phone_is_shared: bool = False

    # Compound keys
    reservation_guest_key: Optional[str] = None
    stay_span_key: Optional[str] = None

    # QA
    is_valid_record: bool = True
    qa_issue: Optional[str] = None
    qa_notes: Optional[str] = None


# ── Spa canonical ────────────────────────────────────────────────────────────

@dataclass
class SpaCanonicalRow:
    """One row per spa appointment.

    Spa is not a financial system for v1 — no cost or revenue fields.
    """
    # Provenance
    source_system: str = ""
    source_file_name: str = ""
    source_row_id: str = ""
    load_timestamp: str = ""

    # Guest name
    guest_name_raw: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name_clean: Optional[str] = None
    match_name_key: Optional[str] = None

    # Activity date/time (canonical matching fields)
    service_date: Optional[date] = None
    service_time: Optional[str] = None
    activity_date: Optional[date] = None
    activity_time: Optional[str] = None

    # Service details
    service_type_raw: Optional[str] = None
    service_name: Optional[str] = None
    duration_mins: Optional[int] = None
    service_category: Optional[str] = None
    is_couples_service: bool = False

    # Guest-level aggregates (populated post-parse)
    guest_total_spa_appts: Optional[int] = None
    guest_total_spa_time_mins: Optional[int] = None
    guest_has_same_day_multi: bool = False
    guest_is_multi_day: bool = False
    guest_has_any_couples: bool = False

    # Group key for back-to-back appointments
    appointment_group_key: Optional[str] = None

    # QA
    is_valid_record: bool = True
    qa_issue: Optional[str] = None
    qa_notes: Optional[str] = None


# ── Dining canonical ─────────────────────────────────────────────────────────

@dataclass
class DiningCanonicalRow:
    """One row per dining reservation or visit.

    Revenue-style columns are explicitly excluded per business rules.
    Dining is not a financial system for v1.
    """
    # Provenance
    source_system: str = ""
    source_file_name: str = ""
    source_row_id: str = ""
    load_timestamp: str = ""

    # Activity date/time
    visit_date: Optional[date] = None
    visit_time: Optional[str] = None
    activity_date: Optional[date] = None
    activity_time: Optional[str] = None

    # Guest name
    guest_name_raw: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name_clean: Optional[str] = None
    match_name_key: Optional[str] = None

    # Phone
    phone_raw: Optional[str] = None
    phone_clean: Optional[str] = None
    match_phone_key: Optional[str] = None

    # Reservation details
    party_size: Optional[int] = None
    dining_status: Optional[str] = None
    table_raw: Optional[str] = None
    dining_area: Optional[str] = None
    booking_source: Optional[str] = None
    server_name: Optional[str] = None

    # Notes / tags
    guest_requests_raw: Optional[str] = None
    visit_notes_raw: Optional[str] = None
    reservation_tags_raw: Optional[str] = None
    guest_tags_raw: Optional[str] = None

    # Guest history
    completed_visits: Optional[int] = None

    # QA
    is_valid_record: bool = True
    qa_issue: Optional[str] = None
    qa_notes: Optional[str] = None
