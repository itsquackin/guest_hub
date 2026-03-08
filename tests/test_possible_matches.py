"""Tests for QA possible-match collection."""
from __future__ import annotations

from datetime import date

import pytest

from src.qa.possible_matches import (
    build_possible_match_issue,
    collect_ambiguous_fuzzy,
    collect_outside_stay_window,
    collect_shared_phone_different_name,
)
from src.models.qa_schema import QaPossibleMatch
from src.matching.exact_match import RoomStayContext
from src.matching.fuzzy_match import FuzzyMatchResult

ACTIVITY_DATE = date(2025, 1, 11)


def _fuzzy_result(name_key: str, score: float = 0.92) -> FuzzyMatchResult:
    stay = RoomStayContext(
        guest_id="G-001",
        match_name_key=name_key,
        arrival_date=date(2025, 1, 10),
        departure_date=date(2025, 1, 13),
    )
    return FuzzyMatchResult(stay=stay, score=score)


class TestBuildPossibleMatchIssue:
    def test_returns_qa_possible_match(self):
        issue = build_possible_match_issue(
            source_system="spa",
            source_activity_key="spa:000001",
            candidate_guest_id="G-001",
            reason="fuzzy_only",
            score=0.91,
        )
        assert isinstance(issue, QaPossibleMatch)

    def test_fields_populated(self):
        issue = build_possible_match_issue(
            source_system="dining",
            source_activity_key="dining:000005",
            candidate_guest_id="G-099",
            reason="same_name_outside_stay_window",
            score=0.95,
            activity_date=ACTIVITY_DATE,
            match_method="FuzzyNameDate",
            left_name_key="smith|john",
            right_name_key="smith|john",
        )
        assert issue.source_system == "dining"
        assert issue.source_activity_key == "dining:000005"
        assert issue.candidate_guest_id == "G-099"
        assert issue.reason == "same_name_outside_stay_window"
        assert issue.match_score == 0.95
        assert issue.activity_date == ACTIVITY_DATE
        assert issue.left_name_key == "smith|john"

    def test_optional_fields_default_to_none(self):
        issue = build_possible_match_issue(
            source_system="spa",
            source_activity_key="spa:000001",
            candidate_guest_id="G-001",
            reason="fuzzy_only",
        )
        assert issue.match_score is None
        assert issue.activity_date is None
        assert issue.left_name_key is None


class TestCollectAmbiguousFuzzy:
    def test_returns_one_issue_per_candidate(self):
        candidates = [
            _fuzzy_result("smith|jon", 0.93),
            _fuzzy_result("smith|joe", 0.91),
        ]
        issues = collect_ambiguous_fuzzy(
            source_system="spa",
            source_activity_key="spa:000001",
            candidates=candidates,
            activity_date=ACTIVITY_DATE,
            left_name_key="smith|john",
        )
        assert len(issues) == 2

    def test_each_issue_is_qa_possible_match(self):
        candidates = [_fuzzy_result("smith|jon")]
        issues = collect_ambiguous_fuzzy(
            source_system="spa",
            source_activity_key="spa:000001",
            candidates=candidates,
        )
        assert all(isinstance(i, QaPossibleMatch) for i in issues)

    def test_reason_is_fuzzy_only(self):
        candidates = [_fuzzy_result("smith|jon")]
        issues = collect_ambiguous_fuzzy(
            source_system="spa",
            source_activity_key="spa:000001",
            candidates=candidates,
        )
        assert issues[0].reason == "fuzzy_only"

    def test_score_preserved(self):
        candidates = [_fuzzy_result("smith|jon", score=0.94)]
        issues = collect_ambiguous_fuzzy(
            source_system="spa",
            source_activity_key="spa:000001",
            candidates=candidates,
        )
        assert issues[0].match_score == pytest.approx(0.94)

    def test_empty_candidates_returns_empty(self):
        issues = collect_ambiguous_fuzzy(
            source_system="spa",
            source_activity_key="spa:000001",
            candidates=[],
        )
        assert issues == []


class TestCollectOutsideStayWindow:
    def test_returns_single_qa_issue(self):
        issue = collect_outside_stay_window(
            source_system="dining",
            source_activity_key="dining:000003",
            guest_id="G-042",
            score=1.0,
            activity_date=ACTIVITY_DATE,
            left_name_key="doe|jane",
            right_name_key="doe|jane",
        )
        assert isinstance(issue, QaPossibleMatch)

    def test_reason_set_correctly(self):
        issue = collect_outside_stay_window(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-001",
            score=None,
        )
        assert issue.reason == "same_name_outside_stay_window"

    def test_guest_id_propagated(self):
        issue = collect_outside_stay_window(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-777",
            score=0.88,
        )
        assert issue.candidate_guest_id == "G-777"


class TestCollectSharedPhoneDifferentName:
    def test_returns_qa_possible_match(self):
        issue = collect_shared_phone_different_name(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-001",
            activity_date=ACTIVITY_DATE,
            left_name_key="doe|jane",
            right_name_key="smith|john",
            phone_key="5551234567",
        )
        assert isinstance(issue, QaPossibleMatch)

    def test_reason_is_shared_phone_different_last_name(self):
        issue = collect_shared_phone_different_name(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-001",
        )
        assert issue.reason == "same_phone_different_last_name"

    def test_phone_key_set_on_both_sides(self):
        issue = collect_shared_phone_different_name(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-001",
            phone_key="5551234567",
        )
        assert issue.left_phone_key == "5551234567"
        assert issue.right_phone_key == "5551234567"

    def test_score_is_none(self):
        issue = collect_shared_phone_different_name(
            source_system="spa",
            source_activity_key="spa:000001",
            guest_id="G-001",
        )
        assert issue.match_score is None
