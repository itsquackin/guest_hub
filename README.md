# Guest Hub

A Python data-engineering pipeline that ingests **Rooms XML**, **Spa PDF**, and **Dining CSV** source files, standardizes them into guest-grain canonical tables, and produces a linked hub of guest identity, phone dimensions, stay facts, and activity bridges — with full QA output for uncertain joins.

---

## Key design decisions

| Rule | Detail |
|---|---|
| Guest grain from the start | Every person (primary + accompanying) gets their own canonical row |
| Financial truth isolation | `fact_room_stay` is one row per `confirmation_number`; no row multiplication from guest expansion |
| Phone inheritance | Accompanying guests inherit the reservation phone; flagged `phone_is_inherited=True, phone_is_shared=True` |
| Revenue columns stripped | 20 dining revenue/financial columns are removed at parse time and never enter canonical tables |
| QA-first matching | Uncertain joins → `qa_possible_matches`; never force-linked |
| Fuzzy flag | Every `FuzzyNameDate` match sets `match_flag_fuzzy=True` in all output tables |
| Date tolerance | Activity date must fall within `arrival − 1 day … departure + 1 day` (configurable) |

---

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline
python run_pipeline.py --config config/settings.yaml

# Optional: export Excel workbook + JSON + archive package
python run_pipeline.py --excel --json --package

# Run the legacy spa calendar converter
python run_spa_legacy.py path/to/spa_calendar.pdf --output spa_output.xlsx
```

---

## Repository structure

```
guest_hub/
├── config/
│   ├── settings.yaml          # 18-stage pipeline config + data paths
│   ├── column_maps.yaml       # XML C-code map + dining column aliases
│   ├── source_rules.yaml      # Per-source file globs + parsing options
│   ├── matching_rules.yaml    # Match method thresholds + signals
│   ├── qa_rules.yaml          # QA check thresholds
│   └── logging.yaml           # Console + rotating-file log configuration
├── data/
│   ├── raw/                   # Input: rooms/, spa/, dining/
│   ├── reference/             # room_types.tsv, special_requests.tsv
│   ├── interim/               # Per-source intermediate outputs
│   ├── processed/
│   │   ├── canonical/         # Guest-grain canonical tables
│   │   ├── hub/               # dim_guest, dim_phone, fact_room_stay, bridges
│   │   └── qa/                # QA issues + possible matches
│   └── archive/               # Run manifests + source snapshots
├── src/
│   ├── cleaners/              # nulls, names, phones, dates, codes, text
│   ├── loaders/               # room, spa, dining, reference file loaders
│   ├── parsers/               # room XML, spa PDF, dining CSV parsers
│   ├── transforms/            # standardize + expand + enrich per source
│   ├── matching/              # stay_window, exact_match, fuzzy_match, scorer
│   ├── qa/                    # name/phone/lookup/duplicate/possible-match checks
│   ├── models/                # canonical_schema, hub_schema, qa_schema, enums
│   ├── pipeline/              # RunContext, stages, orchestrator, manifest builder
│   ├── outputs/               # CSV, Excel, JSON exporters + run packager
│   └── legacy/                # spa_calendar_converter (standalone CLI)
├── tests/                     # 178 unit tests across all layers
├── docs/                      # business_rules, source_dictionary, qa_checklist, runbook
├── run_pipeline.py            # Main pipeline CLI entry point
└── run_spa_legacy.py          # Legacy spa PDF → Excel CLI
```

---

## Pipeline stages

The pipeline runs 18 named stages in order:

1. `load_raw_sources` — discover + load file paths for rooms, spa, dining
2. `load_reference_tables` — load room_types.tsv + special_requests.tsv
3. `parse_rooms_xml` — extract coded XML fields (C9–C135) per reservation
4. `parse_spa_pdf` — extract appointment rows from PDFs (pdfplumber or built-in fallback)
5. `parse_dining_csv` — read CSV, strip revenue columns, map column aliases
6. `standardize_shared_fields` — apply common provenance stamps
7. `expand_room_guests` — split each reservation into primary + accompanying guest rows
8. `enrich_room_lookups` — resolve room-type and special-request codes
9. `write_canonical_outputs` — write rooms/spa/dining canonical CSV files
10. `run_qa_validations` — name, phone, lookup, and duplicate checks
11. `build_guest_phone_dimensions` — resolve `dim_guest` + `dim_phone` from rooms canonical
12. `run_exact_matching` — link spa/dining to room guests by exact `match_name_key` + date window
13. `run_fuzzy_matching` — link remaining records by JaroWinkler similarity ≥ 0.88
14. `apply_support_signals` — add phone-support evidence to match results
15. `build_hub_tables` — write `bridge_guest_activity` + `bridge_guest_room_stay`
16. `build_fact_room_stay` — write one-row-per-confirmation stay-level fact
17. `export_deliverables` — write CSV (+ optional Excel, JSON) outputs
18. `write_run_manifest` — write `qa_run_summary.json`

---

## Matching rules

| Method | Trigger | Flag |
|---|---|---|
| `ExactNameDate` | `match_name_key` equality + activity date within stay window | `match_flag_fuzzy=False` |
| `FuzzyNameDate` | JaroWinkler ≥ 0.88 + date window | `match_flag_fuzzy=True` |
| `PhoneSupport` | Shared phone key + same last name | Adds confidence, does not create new link |
| Ambiguous fuzzy | Top two scores within 0.03 margin | Routed to `qa_possible_matches` |

---

## Testing

```bash
pytest tests/ -q
```

178 tests covering: name/phone cleaning, XML parsing, guest expansion, room enrichment, dining CSV parsing, stay-window logic, fuzzy matching, and QA possible-match collection.

---

## Configuration

All thresholds and file paths are in `config/`. Key settings:

- `settings.yaml` → `date_window_tolerance_days: 1`
- `matching_rules.yaml` → `fuzzy.score_cutoff: 0.88`, `date_window.tolerance_days: 1`
- `qa_rules.yaml` → shared-phone threshold, incomplete-name check toggle

See `docs/business_rules.md` for the full locked rule set and `docs/runbook.md` for operational guidance.
