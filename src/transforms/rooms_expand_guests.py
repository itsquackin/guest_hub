"""Room guest expansion transform.

Converts a reservation-level RoomsCanonicalRow into one or more
guest-grain rows — one for the primary guest plus one per accompanying
guest found in the accompanying_guest_raw field.

Business rules enforced here:
- Every person becomes a full guest row (even incomplete names).
- Incomplete names still produce rows and receive QA flags.
- Accompanying guests inherit the reservation phone when they have none.
- Inherited phones are flagged as phone_is_inherited = True.
- When more than one guest shares the reservation phone it is also
  flagged as phone_is_shared = True.
- Messy or unparseable name segments are preserved raw and flagged.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass

from src.cleaners.names import (
    build_full_name_clean,
    build_match_name_key,
    classify_name_quality,
    normalize_name_part,
    split_accompanying_guest_text,
    split_full_name,
)
from src.models.canonical_schema import RoomsCanonicalRow
from src.utils.constants import (
    GUEST_ROLE_ACCOMPANYING,
    GUEST_ROLE_PRIMARY,
    QA_INCOMPLETE_NAME,
    QA_MULTI_NAME_FIELD,
    QA_ODD_DELIMITER,
)
from src.utils.id_utils import make_reservation_guest_key

logger = logging.getLogger(__name__)


# ── Legacy input dataclass (kept for backward-compat with existing tests) ─────

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
    """Guest-grain room row emitted by expansion logic (legacy API)."""
    confirmation_number: str
    guest_name_raw: str
    guest_role: str
    guest_sequence_in_reservation: int
    is_primary_reservation_guest: bool
    is_expanded_from_accompanying_text: bool
    phone_raw: str | None
    phone_is_inherited: bool
    phone_is_shared: bool


# ── QA flag helpers ───────────────────────────────────────────────────────────

def _qa_flags_for_name(
    first: str | None,
    last: str | None,
    raw_segment: str,
) -> tuple[str | None, str | None]:
    """Return (qa_issue, qa_notes) for a name pair."""
    quality = classify_name_quality(first, last)
    if quality == "both_blank":
        return QA_INCOMPLETE_NAME, f"unparseable_name:{raw_segment!r}"
    if quality in ("last_only", "first_only"):
        return QA_INCOMPLETE_NAME, f"partial_name:{raw_segment!r}"
    return None, None


def _has_odd_delimiter(raw: str | None) -> bool:
    """Detect delimiters unusual for a single-name field (suggests multi-name)."""
    if not raw:
        return False
    import re
    return bool(re.search(r"[;&/]|\band\b", raw, re.IGNORECASE))


# ── Core expansion (canonical API) ───────────────────────────────────────────

def expand_rooms_canonical_row(
    base_row: RoomsCanonicalRow,
) -> list[RoomsCanonicalRow]:
    """Expand one reservation-level row into guest-grain rows.

    Returns at least one row (the primary guest).
    Accompanying guests are added as additional rows with inherited phone
    flags set when the reservation phone is propagated.

    Args:
        base_row: A RoomsCanonicalRow already processed by rooms_standardize.

    Returns:
        A list of guest-grain RoomsCanonicalRow instances.
    """
    rows: list[RoomsCanonicalRow] = []

    # ── Primary guest ─────────────────────────────────────────────────────────
    primary = copy.deepcopy(base_row)
    primary.guest_role = GUEST_ROLE_PRIMARY
    primary.guest_sequence_in_reservation = 1
    primary.is_primary_reservation_guest = True
    primary.is_expanded_from_accompanying_text = False
    primary.phone_is_inherited = False

    # Name from C21 / C24 fields via primary_guest_name_raw
    # The standardize step already put first/last names in the raw fields.
    # Re-derive from primary_guest_name_raw if direct first/last are missing.
    first = normalize_name_part(base_row.first_name) and base_row.first_name
    last = normalize_name_part(base_row.last_name) and base_row.last_name

    # Try to get first/last from primary_guest_name_raw if not set directly
    if not first and not last and base_row.primary_guest_name_raw:
        first, last = split_full_name(base_row.primary_guest_name_raw)

    primary.first_name = first
    primary.last_name = last
    primary.full_name_clean = build_full_name_clean(first, last)
    primary.match_name_key = build_match_name_key(first, last)
    primary.guest_name_raw = base_row.primary_guest_name_raw or primary.full_name_clean

    # QA for primary name
    qa_issue, qa_note = _qa_flags_for_name(first, last, primary.guest_name_raw or "")
    if qa_issue:
        primary.qa_issue = qa_issue
        primary.qa_notes = qa_note
        primary.is_valid_record = False
        logger.warning(
            "Primary guest name issue in %s (conf=%s): %s",
            base_row.source_file_name, base_row.confirmation_number, qa_note,
        )

    primary.reservation_guest_key = make_reservation_guest_key(
        base_row.confirmation_number, 1
    )
    rows.append(primary)

    # ── Accompanying guests ───────────────────────────────────────────────────
    accompanying_raw = base_row.accompanying_guest_raw
    if not accompanying_raw or not accompanying_raw.strip():
        # Mark phone as shared only if there are multiple guests — here just primary
        primary.phone_is_shared = False
        return rows

    segments = split_accompanying_guest_text(accompanying_raw)
    if not segments:
        return rows

    # With ≥1 accompanying guest the phone becomes shared
    primary.phone_is_shared = True

    reservation_phone = base_row.phone_raw

    for seq_offset, segment in enumerate(segments, start=1):
        acc = copy.deepcopy(base_row)
        acc.guest_role = GUEST_ROLE_ACCOMPANYING
        acc.guest_sequence_in_reservation = 1 + seq_offset
        acc.is_primary_reservation_guest = False
        acc.is_expanded_from_accompanying_text = True
        acc.accompanying_guest_raw = accompanying_raw
        acc.primary_guest_name_raw = primary.full_name_clean

        # Parse name from the raw segment
        acc_first, acc_last = split_full_name(segment)
        acc.first_name = acc_first
        acc.last_name = acc_last
        acc.full_name_clean = build_full_name_clean(acc_first, acc_last)
        acc.match_name_key = build_match_name_key(acc_first, acc_last)
        acc.guest_name_raw = segment

        # Phone inheritance
        acc.phone_raw = reservation_phone
        acc.phone_clean = base_row.phone_clean
        acc.match_phone_key = base_row.match_phone_key
        acc.phone_is_inherited = True
        acc.phone_is_shared = True

        # QA for name
        acc_qa_issue, acc_qa_note = _qa_flags_for_name(acc_first, acc_last, segment)

        # Additional QA: odd delimiters within a single segment
        extra_notes: list[str] = []
        if _has_odd_delimiter(segment):
            extra_notes.append(f"{QA_ODD_DELIMITER}:{segment!r}")

        if acc_qa_issue:
            acc.qa_issue = acc_qa_issue
            all_notes = [n for n in [acc_qa_note] + extra_notes if n]
            acc.qa_notes = "; ".join(all_notes) if all_notes else None
            acc.is_valid_record = False
            logger.warning(
                "Accompanying guest name issue in %s (conf=%s, seq=%d): %s",
                base_row.source_file_name,
                base_row.confirmation_number,
                acc.guest_sequence_in_reservation,
                acc.qa_notes,
            )
        elif extra_notes:
            acc.qa_notes = "; ".join(extra_notes)

        acc.reservation_guest_key = make_reservation_guest_key(
            base_row.confirmation_number,
            acc.guest_sequence_in_reservation,
        )
        rows.append(acc)

    logger.debug(
        "Expanded conf=%s into %d guest row(s) (%d accompanying)",
        base_row.confirmation_number, len(rows), len(rows) - 1,
    )
    return rows


# ── Legacy API (kept for backward-compat with existing tests) ─────────────────

def expand_room_guests(reservation: RoomReservationInput) -> list[ExpandedRoomGuest]:
    """Expand one reservation into guest-grain rows (legacy dataclass API).

    Used by existing tests.  New code should call expand_rooms_canonical_row().
    """
    primary_name = build_full_name_clean(
        reservation.primary_first_name,
        reservation.primary_last_name,
    ) or f"{reservation.primary_first_name} {reservation.primary_last_name}".strip()

    segments = split_accompanying_guest_text(reservation.accompanying_guest_raw)
    has_accompanying = bool(segments)

    results: list[ExpandedRoomGuest] = [
        ExpandedRoomGuest(
            confirmation_number=reservation.confirmation_number,
            guest_name_raw=primary_name,
            guest_role=GUEST_ROLE_PRIMARY,
            guest_sequence_in_reservation=1,
            is_primary_reservation_guest=True,
            is_expanded_from_accompanying_text=False,
            phone_raw=reservation.phone_raw,
            phone_is_inherited=False,
            phone_is_shared=has_accompanying,
        )
    ]

    for seq_offset, segment in enumerate(segments, start=1):
        results.append(
            ExpandedRoomGuest(
                confirmation_number=reservation.confirmation_number,
                guest_name_raw=segment,
                guest_role=GUEST_ROLE_ACCOMPANYING,
                guest_sequence_in_reservation=1 + seq_offset,
                is_primary_reservation_guest=False,
                is_expanded_from_accompanying_text=True,
                phone_raw=reservation.phone_raw,
                phone_is_inherited=True,
                phone_is_shared=True,
            )
        )

    return results
