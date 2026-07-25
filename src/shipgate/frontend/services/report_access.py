"""Resolve ReportStore for a UI run (primary root or worktree)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.runtime.report_store import ReportStore

if TYPE_CHECKING:
    from shipgate.frontend.domain.models import RunRecord


def store_for_run(primary_root: Path, run: RunRecord | None) -> ReportStore:
    """Use the worktree ReportStore when the run recorded one; else primary."""
    if run is not None and run.worktree_path:
        return ReportStore(Path(run.worktree_path))
    return ReportStore(Path(primary_root))
