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

## Status

Current implementation is stubbed; scoring and resolvers are TODO.
