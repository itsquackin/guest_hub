# Project Overview

## Purpose

Guest Hub creates a guest-intelligence layer across Rooms, Spa, and Dining source systems.
The design keeps source parsing separate from matching and emphasizes explainable, QA-first links.

## Locked rules from specification

- Rooms source uses coded XML fields (e.g., `C18` confirmation, `C30` arrival, `C33` departure).
- Rooms canonical output is guest-grain, including expanded accompanying guests.
- Room stay financial truth remains in a separate stay-level fact table.
- Matching starts with exact + fuzzy name/date methods and supports additional signals.
- Stay window tolerance is arrival/departure with ±1 day.

## Repository layout

- `config/`: configurable thresholds and rules.
- `data/`: raw, reference, interim, processed, archive zones.
- `src/`: loaders, parsers, transforms, matching, QA, outputs, legacy.
- `tests/`: fixtures and staged unit tests.

## Implementation status

All three phases are complete and the pipeline is MVP-ready:

- **Phase 1 (canonical foundation)**: rooms_canonical, spa_canonical, dining_canonical, room type/specials enrichment, QA name/phone flags
- **Phase 2 (identity + linking)**: dim_guest, dim_phone, bridge_guest_activity, ExactNameDate + FuzzyNameDate matching, QA possible matches, unmatched outputs
- **Phase 3 (reporting-safe stay truth)**: fact_room_stay, bridge_guest_room_stay, run manifest, CSV/Excel/JSON export, archive packaging

Run with: `python run_pipeline.py [--excel] [--json] [--package]`
