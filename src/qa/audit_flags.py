"""Shared audit-flag helpers used across all QA modules."""
from __future__ import annotations


def join_issues(*issues: str | None) -> str | None:
    """Merge non-None issue strings into a semicolon-delimited value."""
    parts = [i.strip() for i in issues if i and i.strip()]
    return "; ".join(parts) if parts else None


def mark_invalid(row, issue: str, note: str | None = None) -> None:
    """Set is_valid_record=False, qa_issue, and qa_notes on *row* in place."""
    row.is_valid_record = False
    row.qa_issue = join_issues(getattr(row, "qa_issue", None), issue)
    if note:
        row.qa_notes = join_issues(getattr(row, "qa_notes", None), note)
