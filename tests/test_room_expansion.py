"""Tests for room guest expansion scaffolding behavior."""

from src.transforms.rooms_expand_guests import RoomReservationInput, expand_room_guests


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
