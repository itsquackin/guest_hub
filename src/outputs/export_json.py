"""JSON export for hub tables."""
from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Any

from src.pipeline.run_context import RunContext
from src.utils.file_utils import ensure_dir

logger = logging.getLogger(__name__)


def _to_serializable(obj: Any) -> Any:
    """Recursively convert dataclass to JSON-serializable dict."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_serializable(v) for k, v in dataclasses.asdict(obj).items()}
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def export_json(ctx: RunContext, filename: str = "guest_hub.json") -> Path:
    """Write a JSON file containing all hub-level tables."""
    out_path = ensure_dir(ctx.hub_dir) / filename
    payload = {
        "run_id": ctx.run_id,
        "dim_guest": [_to_serializable(g) for g in ctx.dim_guests.values()],
        "dim_phone": [_to_serializable(p) for p in ctx.dim_phones.values()],
        "fact_room_stay": [_to_serializable(s) for s in ctx.fact_room_stays],
        "bridge_guest_activity": [_to_serializable(b) for b in ctx.bridge_guest_activity],
        "bridge_guest_room_stay": [_to_serializable(b) for b in ctx.bridge_guest_room_stay],
    }
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    logger.info("JSON export written: %s", out_path)
    return out_path
