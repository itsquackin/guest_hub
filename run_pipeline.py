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
    try:
        import yaml
        with open(config_path) as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        import json
        with open(config_path) as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return {}


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
    config = _load_config(args.config)
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
