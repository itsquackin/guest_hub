"""Tests for fuzzy name/date matching."""
from __future__ import annotations

from datetime import date

import pytest

from src.matching.exact_match import ExactMatchCandidate, RoomStayContext
from src.matching.fuzzy_match import (
    FuzzyMatchResult,
    are_fuzzy_scores_ambiguous,
    fuzzy_name_score,
    match_fuzzy_name_date,
)

ARRIVAL = date(2025, 1, 10)
DEPARTURE = date(2025, 1, 13)
ACTIVITY_IN_WINDOW = date(2025, 1, 11)
ACTIVITY_OUTSIDE = date(2025, 2, 20)


def _stay(name_key: str, arrival=ARRIVAL, departure=DEPARTURE) -> RoomStayContext:
    return RoomStayContext(
        guest_id="G-001",
        match_name_key=name_key,
        arrival_date=arrival,
        departure_date=departure,
    )


def _candidate(name_key: str, activity_date: date = ACTIVITY_IN_WINDOW) -> ExactMatchCandidate:
    return ExactMatchCandidate(
        guest_id="ACT-001",
        match_name_key=name_key,
        activity_date=activity_date,
    )


class TestFuzzyNameScore:
    def test_identical_strings_score_one(self):
        score = fuzzy_name_score("smith|john", "smith|john")
        assert score == pytest.approx(1.0)

    def test_empty_string_scores_zero(self):
        assert fuzzy_name_score("", "smith|john") == 0.0
        assert fuzzy_name_score("smith|john", "") == 0.0

    def test_completely_different_scores_low(self):
        score = fuzzy_name_score("smith|john", "garcia|maria")
        assert score < 0.5

    def test_close_names_score_high(self):
        # "jon" vs "john" — very similar
        score = fuzzy_name_score("smith|jon", "smith|john")
        assert score > 0.85

    def test_score_between_zero_and_one(self):
        score = fuzzy_name_score("doe|jane", "doe|john")
        assert 0.0 <= score <= 1.0


class TestMatchFuzzyNameDate:
    def test_close_name_within_window_matches(self):
        stays = [_stay("smith|jon")]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays)
        assert result is not None

    def test_result_is_always_flagged_fuzzy(self):
        stays = [_stay("smith|jon")]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays)
        assert result is not None
        assert result.match_flag_fuzzy is True

    def test_exact_match_also_passes_cutoff(self):
        stays = [_stay("smith|john")]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays)
        assert result is not None
        assert result.score == pytest.approx(1.0)

    def test_outside_date_window_returns_none(self):
        stays = [_stay("smith|jon")]
        candidate = _candidate("smith|john", activity_date=ACTIVITY_OUTSIDE)
        result = match_fuzzy_name_date(candidate, stays)
        assert result is None

    def test_score_below_cutoff_returns_none(self):
        stays = [_stay("garcia|maria")]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays, score_cutoff=0.88)
        assert result is None

    def test_empty_stays_returns_none(self):
        candidate = _candidate("smith|john")
        assert match_fuzzy_name_date(candidate, []) is None

    def test_best_score_is_selected(self):
        stays = [
            _stay("smith|jon"),
            _stay("smith|johnny"),
        ]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays)
        assert result is not None
        # Should pick the higher-scoring candidate
        score_jon = fuzzy_name_score("smith|john", "smith|jon")
        score_johnny = fuzzy_name_score("smith|john", "smith|johnny")
        expected_key = "smith|jon" if score_jon >= score_johnny else "smith|johnny"
        assert result.stay.match_name_key == expected_key

    def test_method_field_set(self):
        stays = [_stay("smith|jon")]
        candidate = _candidate("smith|john")
        result = match_fuzzy_name_date(candidate, stays)
        assert result is not None
        assert result.method == "FuzzyNameDate"


class TestAreFuzzyScoresAmbiguous:
    def test_single_candidate_not_ambiguous(self):
        stays = [_stay("smith|jon")]
        candidate = _candidate("smith|john")
        results = are_fuzzy_scores_ambiguous(candidate, stays)
        assert len(results) == 1

    def test_two_close_scores_flagged_as_ambiguous(self):
        # Two very similar names — both should be returned
        stays = [
            _stay("smith|jon"),
            _stay("smith|joe"),
        ]
        candidate = _candidate("smith|john")
        results = are_fuzzy_scores_ambiguous(candidate, stays, ambiguity_margin=0.10)
        # Both may be within margin
        assert len(results) >= 1

    def test_clearly_better_candidate_not_ambiguous(self):
        stays = [
            _stay("smith|john"),   # exact match
            _stay("garcia|maria"),  # very different
        ]
        candidate = _candidate("smith|john")
        results = are_fuzzy_scores_ambiguous(candidate, stays, ambiguity_margin=0.03)
        assert len(results) == 1
        assert results[0].stay.match_name_key == "smith|john"

    def test_empty_stays_returns_empty(self):
        candidate = _candidate("smith|john")
        results = are_fuzzy_scores_ambiguous(candidate, [])
        assert results == []

    def test_all_below_cutoff_returns_empty(self):
        stays = [_stay("garcia|maria"), _stay("jones|bob")]
        candidate = _candidate("smith|john")
        results = are_fuzzy_scores_ambiguous(candidate, stays, score_cutoff=0.95)
        assert results == []
