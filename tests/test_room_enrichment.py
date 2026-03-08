"""Tests for room lookup enrichment (room types + special requests)."""
from __future__ import annotations

from src.transforms.rooms_enrich import (
    RoomEnrichmentResult,
    RoomLookupBundle,
    enrich_room_lookups,
)

ROOM_TYPES = {
    "DLX": "Deluxe Room",
    "STD": "Standard Room",
    "STE": "Suite",
    "KNG": "King Room",
}

SPECIALS = {
    "OCA": "Occasion Setup",
    "HNY": "Honeymoon Package",
    "ANN": "Anniversary Package",
    "FLR": "Floor Preference",
}

BUNDLE = RoomLookupBundle(room_type_map=ROOM_TYPES, special_request_map=SPECIALS)


class TestEnrichRoomLookups:
    def test_known_room_type_resolved(self):
        result = enrich_room_lookups("DLX", None, [], BUNDLE)
        assert result.room_type_description == "Deluxe Room"

    def test_known_assigned_room_type_resolved(self):
        result = enrich_room_lookups("DLX", "KNG", [], BUNDLE)
        assert result.assigned_room_type_description == "King Room"

    def test_unknown_room_type_generates_qa_issue(self):
        result = enrich_room_lookups("XYZ", None, [], BUNDLE)
        assert result.room_type_description is None
        assert any("unknown_room_type" in issue for issue in result.qa_lookup_issues)

    def test_unknown_assigned_room_type_generates_qa_issue(self):
        result = enrich_room_lookups("DLX", "ZZZ", [], BUNDLE)
        assert any("unknown_assigned_room_type" in issue for issue in result.qa_lookup_issues)

    def test_known_specials_resolved(self):
        result = enrich_room_lookups(None, None, ["OCA", "HNY"], BUNDLE)
        assert "Occasion Setup" in result.specials_descriptions
        assert "Honeymoon Package" in result.specials_descriptions

    def test_unknown_special_generates_qa_issue(self):
        result = enrich_room_lookups(None, None, ["OCA", "UNK"], BUNDLE)
        assert any("unknown_special_request" in issue for issue in result.qa_lookup_issues)
        assert "Occasion Setup" in result.specials_descriptions

    def test_no_issues_when_all_known(self):
        result = enrich_room_lookups("DLX", "STD", ["HNY", "ANN"], BUNDLE)
        assert result.qa_lookup_issues == []
        assert result.room_type_description == "Deluxe Room"
        assert result.assigned_room_type_description == "Standard Room"
        assert len(result.specials_descriptions) == 2

    def test_none_room_type_produces_no_qa_issue(self):
        result = enrich_room_lookups(None, None, [], BUNDLE)
        assert result.room_type_description is None
        assert result.qa_lookup_issues == []

    def test_empty_specials_list(self):
        result = enrich_room_lookups("STD", None, [], BUNDLE)
        assert result.specials_descriptions == []

    def test_multiple_unknown_codes_each_flagged(self):
        result = enrich_room_lookups("XXX", "YYY", ["AAA", "BBB"], BUNDLE)
        assert len(result.qa_lookup_issues) == 4

    def test_result_type_is_room_enrichment_result(self):
        result = enrich_room_lookups("DLX", None, [], BUNDLE)
        assert isinstance(result, RoomEnrichmentResult)

    def test_specials_descriptions_preserves_order(self):
        result = enrich_room_lookups(None, None, ["ANN", "FLR", "OCA"], BUNDLE)
        assert result.specials_descriptions == [
            "Anniversary Package", "Floor Preference", "Occasion Setup"
        ]
