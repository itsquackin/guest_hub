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

## Implementation note

Current code is intentionally scaffold-level. Each module exposes signatures and TODOs aligned to
Phase 1/2/3 milestones from the project skeleton.
