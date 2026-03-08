"""Guest identity resolution.

Resolves room guest rows and unmatched activity records into the
dim_guest dimension — one row per unique person.
"""
from __future__ import annotations

import logging
from datetime import date

from src.models.canonical_schema import RoomsCanonicalRow
from src.models.hub_schema import DimGuest
from src.utils.constants import (
    IDENTITY_CONFIRMED,
    IDENTITY_PROBABLE,
    SOURCE_DINING,
    SOURCE_ROOMS,
    SOURCE_SPA,
)
from src.utils.id_utils import new_guest_id
from src.matching.scorer import MatchResult, confidence_label

logger = logging.getLogger(__name__)


def resolve_room_guests(
    canonical_rows: list[RoomsCanonicalRow],
) -> dict[str, DimGuest]:
    """Build a dim_guest dict from rooms_canonical rows.

    Groups rows by match_name_key.  When multiple rows share a key the
    best name (longest non-None) is chosen.

    Returns:
        A dict mapping ``match_name_key → DimGuest``.
    """
    from collections import defaultdict
    groups: dict[str, list[RoomsCanonicalRow]] = defaultdict(list)
    for row in canonical_rows:
        key = row.match_name_key or f"__blank__{row.source_row_id}"
        groups[key].append(row)

    guests: dict[str, DimGuest] = {}
    for key, rows in groups.items():
        # Pick best names: prefer rows where both first and last are present
        best = sorted(
            rows,
            key=lambda r: (
                bool(r.first_name and r.last_name),
                len(r.full_name_clean or ""),
            ),
            reverse=True,
        )[0]

        # Date range
        dates = [r.arrival_date for r in rows if r.arrival_date]
        first_seen = min(dates) if dates else None
        last_seen = max(dates) if dates else None

        g = DimGuest(
            guest_id=new_guest_id(),
            best_first_name=best.first_name,
            best_last_name=best.last_name,
            best_full_name=best.full_name_clean,
            canonical_name_key=best.match_name_key,
            first_seen_date=first_seen,
            last_seen_date=last_seen,
            has_room_activity=True,
            room_activity_count=len(rows),
            identity_status=IDENTITY_CONFIRMED,
            name_confidence="high" if (best.first_name and best.last_name) else "low",
        )
        guests[key] = g

    logger.info("Resolved %d unique guest identities from rooms", len(guests))
    return guests


def update_guest_activity_counts(
    guests: dict[str, DimGuest],
    match_results: list[MatchResult],
) -> None:
    """Update has_*/activity_count fields on DimGuest from match results.

    Mutates guests in place.
    """
    # Build lookup: guest_id → DimGuest
    by_id = {g.guest_id: g for g in guests.values()}

    for result in match_results:
        guest = by_id.get(result.guest_id)
        if not guest:
            continue
        if result.source_system == SOURCE_SPA:
            guest.has_spa_activity = True
            guest.spa_activity_count += 1
        elif result.source_system == SOURCE_DINING:
            guest.has_dining_activity = True
            guest.dining_activity_count += 1

        # Update date range
        if result.activity_date:
            if guest.first_seen_date is None or result.activity_date < guest.first_seen_date:
                guest.first_seen_date = result.activity_date
            if guest.last_seen_date is None or result.activity_date > guest.last_seen_date:
                guest.last_seen_date = result.activity_date

        # Room-derived identities remain Confirmed; fuzzy-linked activity does not
        # downgrade confidence in this v1 model.
        if result.match_flag_fuzzy and guest.identity_status == IDENTITY_CONFIRMED:
            guest.identity_status = IDENTITY_CONFIRMED
