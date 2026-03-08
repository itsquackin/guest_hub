"""Tests for stay-window date logic."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.matching.stay_window import days_from_stay, is_within_stay_window

ARRIVAL = date(2025, 1, 10)
DEPARTURE = date(2025, 1, 13)


class TestIsWithinStayWindow:
    def test_date_on_arrival_day(self):
        assert is_within_stay_window(ARRIVAL, ARRIVAL, DEPARTURE) is True

    def test_date_on_departure_day(self):
        assert is_within_stay_window(DEPARTURE, ARRIVAL, DEPARTURE) is True

    def test_date_inside_stay(self):
        mid = date(2025, 1, 11)
        assert is_within_stay_window(mid, ARRIVAL, DEPARTURE) is True

    def test_date_one_day_before_arrival_within_tolerance(self):
        one_before = ARRIVAL - timedelta(days=1)
        assert is_within_stay_window(one_before, ARRIVAL, DEPARTURE, tolerance_days=1) is True

    def test_date_one_day_after_departure_within_tolerance(self):
        one_after = DEPARTURE + timedelta(days=1)
        assert is_within_stay_window(one_after, ARRIVAL, DEPARTURE, tolerance_days=1) is True

    def test_date_two_days_before_outside_tolerance(self):
        two_before = ARRIVAL - timedelta(days=2)
        assert is_within_stay_window(two_before, ARRIVAL, DEPARTURE, tolerance_days=1) is False

    def test_date_two_days_after_outside_tolerance(self):
        two_after = DEPARTURE + timedelta(days=2)
        assert is_within_stay_window(two_after, ARRIVAL, DEPARTURE, tolerance_days=1) is False

    def test_zero_tolerance_exactly_on_arrival(self):
        assert is_within_stay_window(ARRIVAL, ARRIVAL, DEPARTURE, tolerance_days=0) is True

    def test_zero_tolerance_one_day_before_fails(self):
        one_before = ARRIVAL - timedelta(days=1)
        assert is_within_stay_window(one_before, ARRIVAL, DEPARTURE, tolerance_days=0) is False

    def test_two_day_tolerance_expands_window(self):
        two_after = DEPARTURE + timedelta(days=2)
        assert is_within_stay_window(two_after, ARRIVAL, DEPARTURE, tolerance_days=2) is True

    def test_same_day_stay_within(self):
        """Single-night stay: arrival == departure."""
        same_day = date(2025, 2, 1)
        assert is_within_stay_window(same_day, same_day, same_day) is True

    def test_same_day_stay_adjacent(self):
        same_day = date(2025, 2, 1)
        day_after = same_day + timedelta(days=1)
        assert is_within_stay_window(day_after, same_day, same_day, tolerance_days=1) is True

    def test_far_past_date_fails(self):
        ancient = date(2020, 1, 1)
        assert is_within_stay_window(ancient, ARRIVAL, DEPARTURE, tolerance_days=1) is False

    def test_far_future_date_fails(self):
        future = date(2030, 1, 1)
        assert is_within_stay_window(future, ARRIVAL, DEPARTURE, tolerance_days=1) is False


class TestDaysFromStay:
    def test_inside_stay_returns_zero(self):
        mid = date(2025, 1, 11)
        assert days_from_stay(mid, ARRIVAL, DEPARTURE) == 0

    def test_on_arrival_returns_zero(self):
        assert days_from_stay(ARRIVAL, ARRIVAL, DEPARTURE) == 0

    def test_on_departure_returns_zero(self):
        assert days_from_stay(DEPARTURE, ARRIVAL, DEPARTURE) == 0

    def test_one_day_after_departure(self):
        one_after = DEPARTURE + timedelta(days=1)
        assert days_from_stay(one_after, ARRIVAL, DEPARTURE) == 1

    def test_two_days_after_departure(self):
        two_after = DEPARTURE + timedelta(days=2)
        assert days_from_stay(two_after, ARRIVAL, DEPARTURE) == 2

    def test_one_day_before_arrival(self):
        one_before = ARRIVAL - timedelta(days=1)
        assert days_from_stay(one_before, ARRIVAL, DEPARTURE) == -1

    def test_three_days_before_arrival(self):
        three_before = ARRIVAL - timedelta(days=3)
        assert days_from_stay(three_before, ARRIVAL, DEPARTURE) == -3
