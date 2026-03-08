#!/usr/bin/env python3
"""Guest Hub pipeline entry point.

Usage::

    python run_pipeline.py [--config CONFIG] [--log-level LEVEL]

Options:
    --config    Path to settings.yaml (default: config/settings.yaml)
    --log-level Logging level: DEBUG, INFO, WARNING (default: INFO)
    --excel     Also produce an Excel workbook delivery file
    --json      Also produce a JSON export
    --package   Archive the run outputs after completion
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_config(config_path: str) -> dict:
    path = Path(config_path)
    try:
        import yaml
        with open(config_path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        if path.suffix.lower() in {".yaml", ".yml"}:
            print(
                f"PyYAML not installed; using default runtime config for {config_path}",
                file=sys.stderr,
            )
            return {}
        import json
        with open(config_path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return {}


def _load_yaml_file(path: Path) -> dict:
    """Load a YAML config file into a dict; return empty dict if missing."""
    try:
        import yaml
    except ImportError:
        print(f"PyYAML not installed; cannot load YAML config: {path}", file=sys.stderr)
        return {}

    try:
        with open(path) as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        print(f"Config overlay not found: {path}", file=sys.stderr)
        return {}
    except Exception as exc:
        print(f"Unable to load YAML config {path}: {exc}", file=sys.stderr)
        return {}


def _compose_runtime_config(settings_path: str) -> dict:
    """Compose settings with matching/QA/source/column-map config overlays."""
    settings_file = Path(settings_path)
    base = _load_config(str(settings_file))

    candidate_dirs = [settings_file.parent, Path("config")]
    overlay_names = {
        "matching": "matching_rules.yaml",
        "qa": "qa_rules.yaml",
        "source_rules": "source_rules.yaml",
        "column_maps": "column_maps.yaml",
    }
    for key, file_name in overlay_names.items():
        overlay = {}
        for cfg_dir in candidate_dirs:
            candidate = cfg_dir / file_name
            if candidate.exists():
                overlay = _load_yaml_file(candidate)
                break
        base[key] = overlay

    return base


def main() -> int:
    parser = argparse.ArgumentParser(description="Guest Hub pipeline")
    parser.add_argument(
        "--config", default="config/settings.yaml",
        help="Path to settings.yaml",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument(
        "--excel", action="store_true",
        help="Export Excel workbook",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Export JSON hub tables",
    )
    parser.add_argument(
        "--package", action="store_true",
        help="Archive run outputs after completion",
    )
    args = parser.parse_args()

    # Configure logging
    from src.utils.logging_utils import configure_logging
    configure_logging("config/logging.yaml", level=args.log_level)

    from src.utils.logging_utils import get_logger
    logger = get_logger("run_pipeline")
    logger.info("Guest Hub pipeline starting")

    # Load config and build run context
    config = _compose_runtime_config(args.config)
    from src.pipeline.run_context import RunContext
    ctx = RunContext.from_config(config)

    # Build and run pipeline
    from src.pipeline.orchestrator import build_default_pipeline
    pipeline = build_default_pipeline(ctx)
    pipeline.run(ctx)

    # Optional extras
    if args.excel:
        from src.outputs.export_excel import export_excel
        export_excel(ctx)

    if args.json:
        from src.outputs.export_json import export_json
        export_json(ctx)

    if args.package:
        from src.outputs.package_run import package_run
        package_run(ctx)

    # Summary
    logger.info(
        "Run %s complete — rooms:%d spa:%d dining:%d guests:%d errors:%d",
        ctx.run_id,
        len(ctx.rooms_canonical),
        len(ctx.spa_canonical),
        len(ctx.dining_canonical),
        len(ctx.dim_guests),
        len(ctx.errors),
    )
    return 1 if ctx.errors else 0


if __name__ == "__main__":
    sys.exit(main())
