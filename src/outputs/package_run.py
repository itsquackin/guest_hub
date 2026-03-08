"""Bundle one pipeline run's outputs into an archive folder."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from src.pipeline.run_context import RunContext
from src.utils.file_utils import ensure_dir

logger = logging.getLogger(__name__)


def package_run(ctx: RunContext) -> Path:
    """Copy all output files for *ctx.run_id* into an archive subfolder.

    Creates ``data/archive/runs/<run_id>/`` and copies:
    - All CSVs from canonical/, hub/, and qa/ directories.
    - The run manifest JSON.

    Returns the archive directory path.
    """
    archive_dir = ensure_dir(ctx.archive_dir / ctx.run_id)

    source_dirs = [ctx.canonical_dir, ctx.hub_dir, ctx.qa_dir]
    copied = 0
    for src_dir in source_dirs:
        src_path = Path(src_dir)
        if not src_path.exists():
            continue
        for f in src_path.glob("*"):
            if f.is_file():
                dest = archive_dir / f.name
                shutil.copy2(f, dest)
                copied += 1

    logger.info(
        "Packaged %d file(s) for run %s → %s",
        copied, ctx.run_id, archive_dir,
    )
    return archive_dir
