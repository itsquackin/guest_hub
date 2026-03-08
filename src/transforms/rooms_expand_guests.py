"""Room guest expansion stubs.

Transforms reservation-level room rows into guest-grain rows including accompanying guests.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RoomReservationInput:
    """Minimal reservation input fields needed for guest expansion."""

    confirmation_number: str
    primary_first_name: str
    primary_last_name: str
    accompanying_guest_raw: str
    phone_raw: str | None = None


@dataclass(slots=True)
class ExpandedRoomGuest:
    """Guest-grain room row emitted by expansion logic."""

    confirmation_number: str
    guest_name_raw: str
    guest_role: str
    guest_sequence_in_reservation: int
    is_primary_reservation_guest: bool
    is_expanded_from_accompanying_text: bool
    phone_raw: str | None
    phone_is_inherited: bool
    phone_is_shared: bool


def expand_room_guests(reservation: RoomReservationInput) -> list[ExpandedRoomGuest]:
    """Expand one reservation into one-or-many guest-grain rows.

    TODO:
    - split accompanying guest text with robust delimiter handling
    - preserve messy segments and surface QA flags
    - mark inherited/shared phone when propagated to accompanying guests
    """
    primary_name = f"{reservation.primary_first_name} {reservation.primary_last_name}".strip()
    return [
        ExpandedRoomGuest(
            confirmation_number=reservation.confirmation_number,
            guest_name_raw=primary_name,
            guest_role="Primary",
            guest_sequence_in_reservation=1,
            is_primary_reservation_guest=True,
            is_expanded_from_accompanying_text=False,
            phone_raw=reservation.phone_raw,
            phone_is_inherited=False,
            phone_is_shared=False,
        )
    ]
