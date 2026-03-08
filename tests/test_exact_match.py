"""Tests for exact name/date matching stubs."""

from datetime import date

from src.matching.exact_match import ExactMatchCandidate, RoomStayContext, match_exact_name_date


def test_match_exact_name_date_finds_match_within_tolerance() -> None:
    candidate = ExactMatchCandidate(guest_id="g1", match_name_key="jane|doe", activity_date=date(2025, 1, 11))
    stays = [
        RoomStayContext(
            guest_id="g1",
            match_name_key="jane|doe",
            arrival_date=date(2025, 1, 10),
            departure_date=date(2025, 1, 12),
        )
    ]

    match = match_exact_name_date(candidate, stays, tolerance_days=1)

    assert match is not None
    assert match.stay.guest_id == "g1"


def test_match_exact_name_date_returns_none_for_name_mismatch() -> None:
    candidate = ExactMatchCandidate(guest_id="g2", match_name_key="john|roe", activity_date=date(2025, 1, 11))
    stays = [
        RoomStayContext(
            guest_id="g1",
            match_name_key="jane|doe",
            arrival_date=date(2025, 1, 10),
            departure_date=date(2025, 1, 12),
        )
    ]

    assert match_exact_name_date(candidate, stays) is None
