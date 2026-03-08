"""Phone-as-supporting-signal logic.

In v1, phone is never the sole basis for a confident match.
It is a corroborating signal that can elevate confidence when combined
with name/date evidence, or flag candidates for QA review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.utils.constants import (
    MATCH_DIFF_LAST_SHARED_PHONE,
    MATCH_PHONE_SUPPORT,
)


@dataclass(slots=True)
class PhoneMatchCandidate:
    """An activity record available for phone-based signal checking."""
    source_system: str
    source_activity_key: str
    match_name_key: str | None
    match_phone_key: str | None
    activity_date: date | None


@dataclass(slots=True)
class GuestPhoneContext:
    """A resolved guest's phone information used for signal checks."""
    guest_id: str
    match_name_key: str | None
    match_phone_key: str | None
    last_name_key: str | None = None  # last-name portion of name key


def phones_match(
    candidate: PhoneMatchCandidate,
    guest: GuestPhoneContext,
) -> bool:
    """Return True when both candidate and guest have the same non-None phone key."""
    if not candidate.match_phone_key or not guest.match_phone_key:
        return False
    return candidate.match_phone_key == guest.match_phone_key


def find_phone_support_candidates(
    candidate: PhoneMatchCandidate,
    guests: list[GuestPhoneContext],
) -> list[tuple[GuestPhoneContext, str]]:
    """Return guests whose phone matches the candidate, with a reason code.

    Returns a list of ``(guest, reason)`` tuples:
    - ``PhoneSupport``: same phone, same last name (corroborating signal)
    - ``DifferentLastNameSharedPhone``: same phone, different last name (QA flag)
    """
    results: list[tuple[GuestPhoneContext, str]] = []
    if not candidate.match_phone_key:
        return results
    for guest in guests:
        if not phones_match(candidate, guest):
            continue
        # Check whether last names also match
        candidate_last = (
            candidate.match_name_key.split("|", 1)[-1]
            if candidate.match_name_key and "|" in candidate.match_name_key
            else candidate.match_name_key
        )
        guest_last = guest.last_name_key or (
            guest.match_name_key.split("|", 1)[-1]
            if guest.match_name_key and "|" in guest.match_name_key
            else guest.match_name_key
        )
        if candidate_last and guest_last and candidate_last == guest_last:
            reason = MATCH_PHONE_SUPPORT
        else:
            reason = MATCH_DIFF_LAST_SHARED_PHONE
        results.append((guest, reason))
    return results


def detect_shared_phones(
    guests: list[GuestPhoneContext],
    threshold: int = 3,
) -> set[str]:
    """Return the set of phone keys shared by more than *threshold* guests."""
    from collections import Counter
    counts: Counter[str] = Counter()
    for g in guests:
        if g.match_phone_key:
            counts[g.match_phone_key] += 1
    return {phone for phone, count in counts.items() if count > threshold}
