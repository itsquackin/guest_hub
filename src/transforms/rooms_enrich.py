"""Room enrichment stubs for room type and specials lookups."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RoomLookupBundle:
    """In-memory lookups used to enrich room rows."""

    room_type_map: dict[str, str]
    special_request_map: dict[str, str]


@dataclass(slots=True)
class RoomEnrichmentResult:
    """Result of lookup enrichment for a room row."""

    room_type_description: str | None
    assigned_room_type_description: str | None
    specials_descriptions: list[str]
    qa_lookup_issues: list[str]


def enrich_room_lookups(
    room_type_code: str | None,
    assigned_room_type_code: str | None,
    specials_list: list[str],
    lookups: RoomLookupBundle,
) -> RoomEnrichmentResult:
    """Apply room type + specials lookups and capture unknown-code QA issues."""
    qa_issues: list[str] = []
    room_type_description = lookups.room_type_map.get(room_type_code or "")
    if room_type_code and room_type_description is None:
        qa_issues.append(f"unknown_room_type:{room_type_code}")

    assigned_description = lookups.room_type_map.get(assigned_room_type_code or "")
    if assigned_room_type_code and assigned_description is None:
        qa_issues.append(f"unknown_assigned_room_type:{assigned_room_type_code}")

    specials_descriptions: list[str] = []
    for code in specials_list:
        desc = lookups.special_request_map.get(code)
        if desc is None:
            qa_issues.append(f"unknown_special_request:{code}")
            continue
        specials_descriptions.append(desc)

    return RoomEnrichmentResult(
        room_type_description=room_type_description,
        assigned_room_type_description=assigned_description,
        specials_descriptions=specials_descriptions,
        qa_lookup_issues=qa_issues,
    )
