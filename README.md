# Guest Hub

Guest Hub is a Python-based guest intelligence pipeline scaffold that ingests Rooms XML,
Spa PDF, and Dining CSV data, then standardizes and links guest activity with explainable
matching methods.

## Project goals

- Build guest-grain canonical outputs for rooms, spa, and dining.
- Preserve reservation/stay truth separately to avoid financial double-counting.
- Support explainable matching (`ExactNameDate`, `FuzzyNameDate`) with QA-first handling.
- Keep the legacy spa calendar converter script as a first-class project asset.

## Current status

This repository currently contains **starter stubs** only. Core business logic is intentionally
left as TODO work for phased implementation.

## Planned phases

1. Canonical source foundation (`rooms_canonical`, `spa_canonical`, `dining_canonical`).
2. Identity + linking (`dim_guest`, `dim_phone`, `bridge_guest_activity`).
3. Reporting-safe stay truth + packaging (`fact_room_stay`, exports, run manifest).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Key entry points

- `run_pipeline.py`: orchestrates full pipeline stages (stubbed).
- `run_spa_legacy.py`: executes preserved legacy spa conversion flow (stubbed).
