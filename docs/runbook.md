# Runbook

## Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the pipeline

```bash
python run_pipeline.py
```

With options:

```bash
python run_pipeline.py \
    --config config/settings.yaml \
    --log-level INFO \
    --excel \
    --json \
    --package
```

## Dropping source files

| Source | Directory          | Format |
|--------|--------------------|--------|
| Rooms  | `data/raw/rooms/`  | `.xml` |
| Spa    | `data/raw/spa/`    | `.pdf` |
| Dining | `data/raw/dining/` | `.csv` |

Multiple files per directory are supported and processed in sorted order.

## Reading outputs

| Table                    | Location                                      |
|--------------------------|-----------------------------------------------|
| rooms_canonical          | `data/processed/canonical/rooms_canonical.csv`|
| spa_canonical            | `data/processed/canonical/spa_canonical.csv`  |
| dining_canonical         | `data/processed/canonical/dining_canonical.csv`|
| dim_guest                | `data/processed/hub/dim_guest.csv`            |
| fact_room_stay           | `data/processed/hub/fact_room_stay.csv`       |
| bridge_guest_activity    | `data/processed/hub/bridge_guest_activity.csv`|
| QA name issues           | `data/processed/qa/qa_name_issues.csv`        |
| QA phone issues          | `data/processed/qa/qa_phone_issues.csv`       |
| QA possible matches      | `data/processed/qa/qa_possible_matches.csv`   |
| Run manifest             | `data/processed/qa/<run_id>_manifest.json`    |

## Running the legacy spa converter

```bash
python run_spa_legacy.py data/raw/spa/calendar.pdf outputs/spa_calendar.xlsx
```

## Running tests

```bash
pytest
```
