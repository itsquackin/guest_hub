"""Tests for src/cleaners/phones.py"""
from src.cleaners.phones import (
    build_match_phone_key,
    classify_phone,
    is_blank_phone,
    is_incomplete_like,
    is_international_like,
    is_valid_like,
    normalize_phone,
)


class TestNormalizePhone:
    def test_strips_formatting(self):
        assert normalize_phone("(555) 123-4567") == "5551234567"

    def test_none_returns_none(self):
        assert normalize_phone(None) is None

    def test_empty_returns_none(self):
        assert normalize_phone("") is None

    def test_digits_only_passthrough(self):
        assert normalize_phone("5551234567") == "5551234567"

    def test_strips_plus(self):
        assert normalize_phone("+15551234567") == "15551234567"


class TestBuildMatchPhoneKey:
    def test_last_10_digits(self):
        assert build_match_phone_key("15551234567") == "5551234567"

    def test_exact_10_digits(self):
        assert build_match_phone_key("5551234567") == "5551234567"

    def test_too_short_returns_none(self):
        assert build_match_phone_key("12345") is None

    def test_none_returns_none(self):
        assert build_match_phone_key(None) is None


class TestPhoneFlags:
    def test_blank_detection(self):
        assert is_blank_phone(None) is True
        assert is_blank_phone("") is True
        assert is_blank_phone("5551234567") is False

    def test_incomplete(self):
        assert is_incomplete_like("12345") is True
        assert is_incomplete_like("5551234567") is False

    def test_international_plus(self):
        assert is_international_like("15551234567", "+15551234567") is True

    def test_international_digits(self):
        assert is_international_like("441234567890123") is True

    def test_valid(self):
        assert is_valid_like("5551234567") is True
        assert is_valid_like("123") is False

    def test_classify_inherited(self):
        flags = classify_phone("5551234567", "5551234567", is_inherited=True)
        assert "inherited" in flags
        assert "valid" in flags

    def test_classify_blank(self):
        flags = classify_phone(None, None)
        assert flags == ["blank"]
