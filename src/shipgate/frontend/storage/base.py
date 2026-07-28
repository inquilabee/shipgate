"""Storage protocol for report-server runs and findings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shipgate.frontend.domain.models import (
        FindingCategory,
        FindingRecord,
        RunRecord,
        RunStatus,
        RunSummaryRecord,
    )

MAX_RUNS = 50


class Storage(Protocol):
    def create_run(
        self,
        *,
        branch: str,
        suite_id: str,
        worktree_path: str | None = None,
        run_id: str | None = None,
    ) -> RunRecord:
        """Create and persist a queued run."""
        ...

    def get_run(self, run_id: str) -> RunRecord | None:
        """Return a run by id, or None when missing."""
        ...

    def list_runs(self, *, limit: int = 50, branch: str | None = None) -> list[RunRecord]:
        """Return recent runs, optionally filtered by branch."""
        ...

    def update_run(
        self,
        run_id: str,
        *,
        status: RunStatus | None = None,
        worktree_path: str | None = None,
        error_message: str | None = None,
        current_check_id: str | None = None,
        checks_completed: int | None = None,
        checks_total: int | None = None,
        finished: bool = False,
        summary: RunSummaryRecord | None = None,
    ) -> RunRecord:
        """Update run fields and optionally mark finished."""
        ...

    def replace_findings(self, run_id: str, findings: list[FindingRecord]) -> None:
        """Replace all findings for a run."""
        ...

    def list_findings(
        self,
        run_id: str,
        *,
        severity: str | None = None,
        check_id: str | None = None,
        file: str | None = None,
        category: FindingCategory | None = None,
        rule_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FindingRecord]:
        """List findings for a run with optional filters."""
        ...

    def count_findings(
        self,
        run_id: str,
        *,
        severity: str | None = None,
        check_id: str | None = None,
        file: str | None = None,
        category: FindingCategory | None = None,
        rule_id: str | None = None,
    ) -> int:
        """Count findings for a run with optional filters."""
        ...

    def upsert_check_findings(
        self, run_id: str, check_id: str, findings: list[FindingRecord]
    ) -> None:
        """Replace findings for one check within a run."""
        ...

    def previous_completed_run(self, *, branch: str, before_run_id: str) -> RunRecord | None:
        """Return the prior completed run on a branch."""
        ...

    def prune_old_runs(self, keep: int = 50) -> int:
        """Delete oldest runs past the retention limit."""
        ...

    def has_run(self, run_id: str) -> bool:
        """Return whether a run id exists."""
        ...
