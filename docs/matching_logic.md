# Matching Logic

## Primary matching methods

- `ExactNameDate`: exact normalized name + stay/activity date window.
- `FuzzyNameDate`: near-name + stay/activity date window, always visibly flagged.

## Supporting signals

- Phone support (never sole truth in v1)
- Same name outside stay window
- Repeated cross-source patterns over time
- Same-last/similar-first patterns
- Shared phone with different last names

## Date rule

Room-linking stay windows use arrival through departure, with ±1 day tolerance.

## Explainability requirement

Matching should output method, score, and supporting flags so each link can be audited.
Uncertain links should flow into QA outputs instead of forced joins.

## Implementation status

**Fully implemented.** The matching layer runs in production as part of the 18-stage pipeline.

Key modules:
- `src/matching/keys.py` — `make_name_key()`, `make_phone_key()`, activity source keys
- `src/matching/stay_window.py` — `is_within_stay_window()` (arrival ±1 day through departure ±1 day)
- `src/matching/exact_match.py` — `match_exact_name_date()` returns `ExactMatchResult(score=1.0, match_flag_fuzzy=False)`
- `src/matching/fuzzy_match.py` — `match_fuzzy_name_date()` (JaroWinkler ≥ 0.88, rapidfuzz preferred); `are_fuzzy_scores_ambiguous()` routes to QA when top candidates within 0.03 margin
- `src/matching/scorer.py` — `MatchResult` dataclass with full explainability payload; `confidence_label()` → high/medium/low
- `src/matching/phone_support.py` — `find_phone_support_candidates()` returning `PhoneSupport` or `DifferentLastNameSharedPhone` reason
- `src/matching/guest_resolver.py` — `resolve_room_guests()` builds `dim_guest` dict from rooms canonical; `update_guest_activity_counts()` mutates counts after matching
