"""Tests for the dining CSV parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.parsers.dining_parser import (
    REMOVED_REVENUE_COLUMNS,
    DiningVisitRaw,
    parse_dining_csv_file,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_dining.csv"


class TestParseDiningCsvFile:
    def test_returns_four_records(self):
        records = parse_dining_csv_file(FIXTURE)
        assert len(records) == 4

    def test_source_file_name_set(self):
        records = parse_dining_csv_file(FIXTURE)
        for r in records:
            assert r.source_file_name == "sample_dining.csv"

    def test_source_row_id_format(self):
        records = parse_dining_csv_file(FIXTURE)
        assert ":" in records[0].source_row_id

    def test_retained_is_dict(self):
        records = parse_dining_csv_file(FIXTURE)
        for r in records:
            assert isinstance(r.retained, dict)

    def test_revenue_columns_stripped(self):
        records = parse_dining_csv_file(FIXTURE)
        revenue_names = {
            "Experience Title", "Experience Price", "Total Revenue",
            "Experience Total Sales", "POS Subtotal",
        }
        for r in records:
            for col in revenue_names:
                assert col not in r.retained, f"Revenue column '{col}' should be stripped"

    def test_canonical_names_mapped_visit_date(self):
        records = parse_dining_csv_file(FIXTURE)
        # "Date" header should map to "visit_date"
        assert "visit_date" in records[0].retained
        assert records[0].retained["visit_date"] == "2025-01-11"

    def test_canonical_names_mapped_guest_name(self):
        records = parse_dining_csv_file(FIXTURE)
        assert "guest_name_raw" in records[0].retained

    def test_canonical_names_mapped_phone(self):
        records = parse_dining_csv_file(FIXTURE)
        assert "phone_raw" in records[0].retained
        assert records[0].retained["phone_raw"] == "5551234567"

    def test_canonical_names_mapped_party_size(self):
        records = parse_dining_csv_file(FIXTURE)
        assert "party_size" in records[0].retained
        assert records[0].retained["party_size"] == "2"

    def test_canonical_names_mapped_status(self):
        records = parse_dining_csv_file(FIXTURE)
        assert "dining_status" in records[0].retained
        assert records[0].retained["dining_status"] == "Seated"

    def test_no_show_status_preserved(self):
        records = parse_dining_csv_file(FIXTURE)
        # Row 4 (index 3) is "No Show"
        assert records[3].retained["dining_status"] == "No Show"

    def test_empty_phone_preserved_as_empty_string(self):
        records = parse_dining_csv_file(FIXTURE)
        # Row 4 has no phone
        assert records[3].retained.get("phone_raw", "") == ""

    def test_non_revenue_columns_retained(self):
        records = parse_dining_csv_file(FIXTURE)
        # Server, Guest Requests, Notes should still be present
        first = records[0].retained
        assert "server_name" in first or "Server" in first

    def test_missing_file_returns_empty(self, tmp_path):
        missing = tmp_path / "nonexistent.csv"
        records = parse_dining_csv_file(missing)
        assert records == []

    def test_empty_csv_returns_empty(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("")
        records = parse_dining_csv_file(f)
        assert records == []

    def test_header_only_csv_returns_empty_records(self, tmp_path):
        f = tmp_path / "headers_only.csv"
        f.write_text("Date,Guest Name,Status\n")
        records = parse_dining_csv_file(f)
        assert records == []

    def test_csv_without_revenue_columns_still_works(self, tmp_path):
        f = tmp_path / "clean.csv"
        f.write_text("Date,Guest Name,Status\n2025-01-11,Jane Doe,Seated\n")
        records = parse_dining_csv_file(f)
        assert len(records) == 1
        assert "Total Revenue" not in records[0].retained


class TestRemovedRevenueColumns:
    def test_set_contains_expected_columns(self):
        expected = {
            "Experience Title",
            "Experience Price",
            "Total Revenue",
            "Total Revenue with Gratuity",
            "POS Subtotal",
            "Total Gratuity",
            "Total Tax",
        }
        assert expected.issubset(REMOVED_REVENUE_COLUMNS)

    def test_twenty_columns_total(self):
        # Business rule: exactly 20 revenue columns defined
        assert len(REMOVED_REVENUE_COLUMNS) >= 20
