"""File system utilities for the Guest Hub pipeline."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator


def ensure_dir(path: str | Path) -> Path:
    """Create *path* (and any missing parents) if it does not exist.

    Returns the resolved ``Path`` object.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_files(directory: str | Path, pattern: str) -> list[Path]:
    """Return a sorted list of files matching *pattern* under *directory*.

    Returns an empty list when *directory* does not exist.
    """
    p = Path(directory)
    if not p.exists():
        return []
    return sorted(p.glob(pattern))


def safe_stem(path: str | Path) -> str:
    """Return the file stem (name without extension) for *path*."""
    return Path(path).stem


def iter_files(directory: str | Path, *extensions: str) -> Iterator[Path]:
    """Yield files with the given extensions under *directory*, sorted.

    Example::

        for f in iter_files("data/raw/rooms", ".xml"):
            ...
    """
    p = Path(directory)
    if not p.exists():
        return
    for ext in extensions:
        ext = ext if ext.startswith(".") else f".{ext}"
        yield from sorted(p.glob(f"*{ext}"))


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    """Read a TSV file and return a list of row dicts.

    Skips rows where all values are blank.
    """
    results: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if any(v.strip() for v in row.values()):
                results.append(dict(row))
    return results


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts."""
    results: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            results.append(dict(row))
    return results
