"""Tests for src/cleaners/names.py"""
import pytest
from src.cleaners.names import (
    build_match_name_key,
    build_full_name_clean,
    classify_name_quality,
    normalize_name_part,
    split_accompanying_guest_text,
    split_full_name,
)


class TestNormalizeNamePart:
    def test_basic_lowercase(self):
        assert normalize_name_part("Smith") == "smith"

    def test_strips_accents(self):
        assert normalize_name_part("Müller") == "muller"

    def test_strips_salutation(self):
        assert normalize_name_part("Dr. Jane") == "jane"

    def test_strips_suffix(self):
        assert normalize_name_part("John Jr") == "john"

    def test_none_returns_none(self):
        assert normalize_name_part(None) is None

    def test_blank_returns_none(self):
        assert normalize_name_part("  ") is None

    def test_na_returns_none(self):
        assert normalize_name_part("N/A") is None


class TestBuildMatchNameKey:
    def test_standard_key(self):
        assert build_match_name_key("Jane", "Doe") == "jane|doe"

    def test_blank_first(self):
        assert build_match_name_key(None, "Smith") == "|smith"

    def test_blank_last(self):
        assert build_match_name_key("John", None) == "john|"

    def test_both_blank_returns_none(self):
        assert build_match_name_key(None, None) is None

    def test_accents_stripped(self):
        assert build_match_name_key("José", "García") == "jose|garcia"


class TestSplitFullName:
    def test_comma_format(self):
        first, last = split_full_name("Smith, John")
        assert first == "John" and last == "Smith"

    def test_space_format(self):
        first, last = split_full_name("John Smith")
        assert first == "John" and last == "Smith"

    def test_single_token(self):
        first, last = split_full_name("Smith")
        assert first is None and last == "Smith"

    def test_three_tokens(self):
        first, last = split_full_name("John A Smith")
        assert first == "John A" and last == "Smith"

    def test_none_returns_none_none(self):
        assert split_full_name(None) == (None, None)


class TestSplitAccompanyingGuestText:
    def test_comma_separated(self):
        result = split_accompanying_guest_text("Jane Smith, Bob Jones")
        assert result == ["Jane Smith", "Bob Jones"]

    def test_and_separator(self):
        result = split_accompanying_guest_text("Jane Smith and Bob Jones")
        assert result == ["Jane Smith", "Bob Jones"]

    def test_ampersand_separator(self):
        result = split_accompanying_guest_text("Jane Smith & Bob Jones")
        assert result == ["Jane Smith", "Bob Jones"]

    def test_empty_returns_empty(self):
        assert split_accompanying_guest_text("") == []

    def test_none_returns_empty(self):
        assert split_accompanying_guest_text(None) == []

    def test_single_name(self):
        assert split_accompanying_guest_text("Jane Smith") == ["Jane Smith"]


class TestClassifyNameQuality:
    def test_ok(self):
        assert classify_name_quality("John", "Smith") == "ok"

    def test_last_only(self):
        assert classify_name_quality(None, "Smith") == "last_only"

    def test_first_only(self):
        assert classify_name_quality("John", None) == "first_only"

    def test_both_blank(self):
        assert classify_name_quality(None, None) == "both_blank"
