"""Tests for the spa PDF parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.parsers.spa_parser import SpaAppointmentRaw, parse_spa_pdf_file


class TestParseSpaParserContract:
    """Test that the parser returns the right types without requiring a real PDF."""

    def test_missing_file_returns_empty(self, tmp_path):
        missing = tmp_path / "nonexistent.pdf"
        records = parse_spa_pdf_file(missing)
        assert records == []

    def test_non_pdf_binary_returns_empty_or_list(self, tmp_path):
        f = tmp_path / "fake.pdf"
        f.write_bytes(b"this is not a pdf")
        records = parse_spa_pdf_file(f)
        assert isinstance(records, list)

    def test_return_type_is_list(self, tmp_path):
        f = tmp_path / "empty.pdf"
        f.write_bytes(b"%PDF-1.4\n%%EOF\n")
        records = parse_spa_pdf_file(f)
        assert isinstance(records, list)

    def test_each_record_is_spa_appointment_raw(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4\n%%EOF\n")
        records = parse_spa_pdf_file(f)
        for r in records:
            assert isinstance(r, SpaAppointmentRaw)


class TestSpaAppointmentRawDataclass:
    def test_can_instantiate_with_required_fields(self):
        record = SpaAppointmentRaw(
            source_file_name="test.pdf",
            source_row_id="test:000001",
            guest_name_raw="Jane Doe",
            service_date_raw="2025-01-11",
            service_time_raw="10:00 AM",
            service_name_raw="Swedish Massage",
        )
        assert record.source_file_name == "test.pdf"
        assert record.source_row_id == "test:000001"
        assert record.guest_name_raw == "Jane Doe"
        assert record.service_date_raw == "2025-01-11"
        assert record.service_time_raw == "10:00 AM"
        assert record.service_name_raw == "Swedish Massage"

    def test_duration_defaults_to_empty_string(self):
        record = SpaAppointmentRaw(
            source_file_name="spa.pdf",
            source_row_id="spa:000001",
            guest_name_raw="Jane Doe",
            service_date_raw="2025-01-11",
            service_time_raw="10:00 AM",
            service_name_raw="Facial",
        )
        assert record.duration_raw == ""

    def test_therapist_defaults_to_empty_string(self):
        record = SpaAppointmentRaw(
            source_file_name="spa.pdf",
            source_row_id="spa:000001",
            guest_name_raw="Jane Doe",
            service_date_raw="2025-01-11",
            service_time_raw="10:00 AM",
            service_name_raw="Facial",
        )
        assert record.therapist_raw == ""

    def test_duration_can_be_set(self):
        record = SpaAppointmentRaw(
            source_file_name="spa.pdf",
            source_row_id="spa:000001",
            guest_name_raw="Jane Doe",
            service_date_raw="2025-01-11",
            service_time_raw="10:00 AM",
            service_name_raw="Massage",
            duration_raw="60 min",
        )
        assert record.duration_raw == "60 min"
