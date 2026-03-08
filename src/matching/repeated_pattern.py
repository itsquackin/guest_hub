"""Repeated cross-source pattern detection.

Identifies guests who appear repeatedly in spa or dining without a room match,
which may indicate a local guest, a loyal non-room visitor, or an identity
that should be unified with a room guest.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class ActivityRecord:
    """Minimal activity record for pattern analysis."""
    source_system: str
    source_activity_key: str
    match_name_key: str | None
    match_phone_key: str | None
    activity_date: date | None


@dataclass
class RepeatedPattern:
    """Summary of a repeated cross-source guest pattern."""
    match_name_key: str
    total_activities: int
    source_systems: list[str]
    date_range_days: int
    activity_keys: list[str]
    is_multi_system: bool


def find_repeated_patterns(
    unmatched: list[ActivityRecord],
    min_occurrences: int = 2,
) -> list[RepeatedPattern]:
    """Find guests with repeated activity in unmatched records.

    Groups unmatched records by match_name_key and returns patterns where
    the guest appears at least *min_occurrences* times.

    Args:
        unmatched: List of activity records not linked to any room guest.
        min_occurrences: Minimum number of appearances to flag as a pattern.

    Returns:
        List of RepeatedPattern objects describing recurring unmatched guests.
    """
    by_name: dict[str, list[ActivityRecord]] = defaultdict(list)
    for rec in unmatched:
        if rec.match_name_key:
            by_name[rec.match_name_key].append(rec)

    patterns: list[RepeatedPattern] = []
    for name_key, records in by_name.items():
        if len(records) < min_occurrences:
            continue
        dates = [r.activity_date for r in records if r.activity_date]
        date_range = 0
        if len(dates) >= 2:
            date_range = (max(dates) - min(dates)).days
        systems = list({r.source_system for r in records})
        patterns.append(
            RepeatedPattern(
                match_name_key=name_key,
                total_activities=len(records),
                source_systems=systems,
                date_range_days=date_range,
                activity_keys=[r.source_activity_key for r in records],
                is_multi_system=len(systems) > 1,
            )
        )

    return sorted(patterns, key=lambda p: p.total_activities, reverse=True)
