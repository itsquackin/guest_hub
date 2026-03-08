"""Tests for the room XML parser."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.parsers.room_parser import (
    ROOM_CODE_MAP,
    RoomRawRecord,
    _detect_strategy,
    parse_room_xml_file,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_room.xml"


# ── Fixture-based tests ───────────────────────────────────────────────────────

class TestParseRoomXmlFile:
    def test_returns_three_records(self):
        records = parse_room_xml_file(FIXTURE)
        assert len(records) == 3

    def test_all_have_confirmation_numbers(self):
        records = parse_room_xml_file(FIXTURE)
        conf_nums = [r.fields["confirmation_number"] for r in records]
        assert conf_nums == ["RES-001", "RES-002", "RES-003"]

    def test_first_record_last_name(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["last_name_raw"] == "Smith"

    def test_first_record_first_name(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["first_name_raw"] == "John"

    def test_accompanying_guest_field_parsed(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["accompanying_guest_raw"] == "Jane Smith, Bob Johnson"

    def test_accompanying_guest_ampersand_variant(self):
        records = parse_room_xml_file(FIXTURE)
        # XML entity &amp; should be decoded to &
        assert "Carlos Garcia" in records[2].fields["accompanying_guest_raw"]

    def test_empty_accompanying_field(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[1].fields.get("accompanying_guest_raw", "") == ""

    def test_source_file_name_set(self):
        records = parse_room_xml_file(FIXTURE)
        for r in records:
            assert r.source_file_name == "sample_room.xml"

    def test_source_row_id_format(self):
        records = parse_room_xml_file(FIXTURE)
        # format: "stem:000001"
        assert records[0].source_row_id.startswith("sample_room")
        assert ":" in records[0].source_row_id

    def test_phone_field(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["phone_raw"] == "5551234567"

    def test_nightly_rate_field(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["nightly_rate_raw"] == "250.00"

    def test_room_type_code_field(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["room_type_code"] == "DLX"
        assert records[1].fields["room_type_code"] == "STD"

    def test_specials_raw_field(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["specials_raw"] == "OCA,HNY"

    def test_arrival_and_departure_raw(self):
        records = parse_room_xml_file(FIXTURE)
        assert records[0].fields["arrival_raw"] == "2025-01-10"
        assert records[0].fields["departure_raw"] == "2025-01-13"


class TestParseRoomXmlFileEdgeCases:
    def test_missing_file_returns_empty(self, tmp_path):
        missing = tmp_path / "nonexistent.xml"
        records = parse_room_xml_file(missing)
        assert records == []

    def test_malformed_xml_returns_empty(self, tmp_path):
        bad = tmp_path / "bad.xml"
        bad.write_text("<rooms><room><C18>RES999</C18></room")  # no closing tag
        records = parse_room_xml_file(bad)
        assert records == []

    def test_record_without_confirmation_number_is_skipped(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <rooms>
                <room><C21>Smith</C21><C24>Jane</C24></room>
                <room><C18>RES-X</C18><C21>Doe</C21><C24>John</C24></room>
            </rooms>
        """)
        f = tmp_path / "test.xml"
        f.write_text(xml)
        records = parse_room_xml_file(f)
        assert len(records) == 1
        assert records[0].fields["confirmation_number"] == "RES-X"

    def test_attribute_strategy_detected_and_parsed(self, tmp_path):
        xml = textwrap.dedent("""\
            <?xml version="1.0" encoding="UTF-8"?>
            <rooms>
                <room>
                    <Field id="C18">RES-ATTR</Field>
                    <Field id="C21">Jones</Field>
                    <Field id="C24">Alice</Field>
                </room>
            </rooms>
        """)
        f = tmp_path / "attr_test.xml"
        f.write_text(xml)
        records = parse_room_xml_file(f)
        assert len(records) == 1
        assert records[0].fields["confirmation_number"] == "RES-ATTR"
        assert records[0].fields["last_name_raw"] == "Jones"

    def test_empty_rooms_file_returns_empty(self, tmp_path):
        xml = '<?xml version="1.0" encoding="UTF-8"?><rooms></rooms>'
        f = tmp_path / "empty.xml"
        f.write_text(xml)
        records = parse_room_xml_file(f)
        assert records == []


class TestRoomCodeMap:
    def test_code_map_has_expected_codes(self):
        expected_codes = {"C18", "C21", "C24", "C27", "C30", "C33", "C93"}
        assert expected_codes.issubset(ROOM_CODE_MAP.keys())

    def test_confirmation_number_code(self):
        assert ROOM_CODE_MAP["C18"] == "confirmation_number"

    def test_accompanying_guest_code(self):
        assert ROOM_CODE_MAP["C27"] == "accompanying_guest_raw"
