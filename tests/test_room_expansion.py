"""Tests for room guest expansion — both legacy and canonical APIs."""
from __future__ import annotations

from src.transforms.rooms_expand_guests import (
    ExpandedRoomGuest,
    RoomReservationInput,
    expand_room_guests,
    expand_rooms_canonical_row,
)
from src.models.canonical_schema import RoomsCanonicalRow


# ── Legacy API tests (backward-compat) ───────────────────────────────────────

def test_expand_room_guests_returns_primary_row_by_default() -> None:
    reservation = RoomReservationInput(
        confirmation_number="ABC123",
        primary_first_name="Jane",
        primary_last_name="Doe",
        accompanying_guest_raw="",
        phone_raw="5551234567",
    )
    rows = expand_room_guests(reservation)
    assert len(rows) == 1
    assert rows[0].guest_role == "Primary"
    assert rows[0].is_primary_reservation_guest is True
    assert rows[0].phone_is_inherited is False


def test_single_guest_phone_is_not_shared() -> None:
    reservation = RoomReservationInput(
        confirmation_number="ABC123",
        primary_first_name="Jane",
        primary_last_name="Doe",
        accompanying_guest_raw="",
        phone_raw="5551234567",
    )
    rows = expand_room_guests(reservation)
    assert rows[0].phone_is_shared is False


def test_accompanying_guest_creates_two_rows() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-001",
        primary_first_name="John",
        primary_last_name="Smith",
        accompanying_guest_raw="Jane Smith",
        phone_raw="5551234567",
    )
    rows = expand_room_guests(reservation)
    assert len(rows) == 2


def test_accompanying_guest_inherits_phone() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-001",
        primary_first_name="John",
        primary_last_name="Smith",
        accompanying_guest_raw="Jane Smith",
        phone_raw="5551234567",
    )
    rows = expand_room_guests(reservation)
    acc = rows[1]
    assert acc.phone_raw == "5551234567"
    assert acc.phone_is_inherited is True
    assert acc.phone_is_shared is True


def test_primary_phone_shared_when_accompanying_present() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-001",
        primary_first_name="John",
        primary_last_name="Smith",
        accompanying_guest_raw="Jane Smith",
        phone_raw="5551234567",
    )
    rows = expand_room_guests(reservation)
    primary = rows[0]
    assert primary.phone_is_shared is True
    assert primary.phone_is_inherited is False


def test_two_accompanying_guests_comma_separated() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-002",
        primary_first_name="Maria",
        primary_last_name="Garcia",
        accompanying_guest_raw="Carlos Garcia, Anna Martinez",
        phone_raw="5557654321",
    )
    rows = expand_room_guests(reservation)
    assert len(rows) == 3
    assert rows[1].guest_role == "Accompanying"
    assert rows[2].guest_role == "Accompanying"


def test_ampersand_delimiter_splits_correctly() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-003",
        primary_first_name="Alice",
        primary_last_name="Brown",
        accompanying_guest_raw="Bob Brown & Carol Brown",
        phone_raw="5559876543",
    )
    rows = expand_room_guests(reservation)
    assert len(rows) == 3


def test_sequence_numbers_are_unique() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-004",
        primary_first_name="Tom",
        primary_last_name="Wilson",
        accompanying_guest_raw="Sue Wilson, Kim Wilson",
        phone_raw="5554444444",
    )
    rows = expand_room_guests(reservation)
    seqs = [r.guest_sequence_in_reservation for r in rows]
    assert len(seqs) == len(set(seqs)), "Sequence numbers must be unique"
    assert 1 in seqs


def test_no_phone_primary_guest() -> None:
    reservation = RoomReservationInput(
        confirmation_number="RES-005",
        primary_first_name="Jim",
        primary_last_name="Doe",
        accompanying_guest_raw="",
        phone_raw=None,
    )
    rows = expand_room_guests(reservation)
    assert rows[0].phone_raw is None


# ── Canonical API tests (RoomsCanonicalRow) ────────────────────────────────

def _make_base_row(**kwargs) -> RoomsCanonicalRow:
    """Construct a minimal RoomsCanonicalRow for expansion tests."""
    defaults = dict(
        source_system="rooms",
        source_file_name="test.xml",
        source_row_id="test:000001",
        confirmation_number="CONF-001",
        first_name="Jane",
        last_name="Doe",
        primary_guest_name_raw="Jane Doe",
        accompanying_guest_raw="",
        phone_raw="5551234567",
        phone_clean="5551234567",
        match_phone_key="5551234567",
    )
    defaults.update(kwargs)
    return RoomsCanonicalRow(**defaults)


def test_canonical_expand_primary_only():
    base = _make_base_row()
    rows = expand_rooms_canonical_row(base)
    assert len(rows) == 1
    assert rows[0].is_primary_reservation_guest is True
    assert rows[0].phone_is_inherited is False
    assert rows[0].phone_is_shared is False


def test_canonical_expand_with_accompanying():
    base = _make_base_row(accompanying_guest_raw="Bob Smith")
    rows = expand_rooms_canonical_row(base)
    assert len(rows) == 2
    primary, acc = rows
    assert primary.is_primary_reservation_guest is True
    assert primary.phone_is_shared is True
    assert acc.is_primary_reservation_guest is False
    assert acc.is_expanded_from_accompanying_text is True
    assert acc.phone_is_inherited is True
    assert acc.phone_is_shared is True


def test_canonical_expand_match_name_key_set():
    base = _make_base_row()
    rows = expand_rooms_canonical_row(base)
    assert rows[0].match_name_key == "jane|doe"


def test_canonical_expand_accompanying_name_parsed():
    base = _make_base_row(accompanying_guest_raw="Alice Smith")
    rows = expand_rooms_canonical_row(base)
    acc = rows[1]
    assert acc.first_name == "Alice"
    assert acc.last_name == "Smith"


def test_canonical_expand_reservation_guest_key_unique():
    base = _make_base_row(accompanying_guest_raw="Bob Smith, Carol Smith")
    rows = expand_rooms_canonical_row(base)
    keys = [r.reservation_guest_key for r in rows]
    assert len(keys) == len(set(keys)), "reservation_guest_key must be unique per expansion"


def test_canonical_expand_incomplete_name_flagged():
    """Accompanying guest with blank/unparseable name still becomes a row with QA flag."""
    base = _make_base_row(accompanying_guest_raw="???")
    rows = expand_rooms_canonical_row(base)
    assert len(rows) == 2
    acc = rows[1]
    assert acc.qa_issue is not None


def test_canonical_expand_phone_inherited_from_reservation():
    base = _make_base_row(
        phone_raw="5559999999",
        phone_clean="5559999999",
        match_phone_key="5559999999",
        accompanying_guest_raw="Guest Two",
    )
    rows = expand_rooms_canonical_row(base)
    acc = rows[1]
    assert acc.phone_raw == "5559999999"
    assert acc.phone_is_inherited is True
