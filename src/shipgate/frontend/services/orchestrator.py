"""Background suite-run orchestration for the report server."""

from __future__ import annotations

import threading
from contextlib import suppress
from functools import partial
from pathlib import Path

from shipgate.app import RunCommand, RunProgress, ShipGateApp
from shipgate.domain.modes import RunMode
from shipgate.frontend.domain.models import RunRecord, RunStatus
from shipgate.frontend.domain.requirements import is_acknowledged
from shipgate.frontend.services.ingest import (
    ingest_check_into_storage,
    ingest_run_report,
)
from shipgate.frontend.services.worktree import WorktreeError, WorktreeManager
from shipgate.frontend.storage.base import MAX_RUNS, Storage
from shipgate.runtime.install import install_suite
from shipgate.runtime.reports import generate_run_id


class OrchestratorError(Exception):
    """Raised when a run cannot be started."""


class RunOrchestrator:
    def __init__(
        self, primary_root: Path, storage: Storage, app: ShipGateApp | None = None
    ) -> None:
        self._primary_root = Path(primary_root).resolve()
        self._storage = storage
        self._app = app or ShipGateApp()
        self._lock = threading.Lock()
        self._active_run_id: str | None = None
        self._cancel_events: dict[str, threading.Event] = {}
        self._done = threading.Event()
        self._done.set()
        self._fail_stale_runs()

    def wait(self, timeout: float | None = None) -> bool:
        return self._done.wait(timeout)

    def start_run(
        self,
        branch: str,
        suite_id: str,
        *,
        check: str | None = None,
        changed_only: bool = False,
        since: str | None = None,
    ) -> RunRecord:
        if not is_acknowledged(self._primary_root):
            raise OrchestratorError("acknowledge requirements before starting a run")

        with self._lock:
            if self._active_run_id is not None or self._has_active_run():
                raise OrchestratorError("a run is already active")

            run_id = generate_run_id()
            run = self._storage.create_run(branch=branch, suite_id=suite_id, run_id=run_id)
            self._active_run_id = run.id
            self._cancel_events[run.id] = threading.Event()
            self._done.clear()
            thread = threading.Thread(
                target=self._execute_run,
                kwargs={
                    "run_id": run.id,
                    "branch": branch,
                    "suite_id": suite_id,
                    "check": check,
                    "changed_only": changed_only,
                    "since": since,
                },
                daemon=True,
                name=f"shipgate-run-{run.id}",
            )
            thread.start()
            return run

    def request_cancel(self, run_id: str) -> bool:
        event = self._cancel_events.get(run_id)
        if event is None:
            run = self._storage.get_run(run_id)
            if run is None or run.status not in (RunStatus.QUEUED, RunStatus.RUNNING):
                return False
            event = threading.Event()
            self._cancel_events[run_id] = event
        event.set()
        return True

    def _fail_stale_runs(self) -> None:
        for run in self._storage.list_runs(limit=MAX_RUNS):
            if run.status in (RunStatus.QUEUED, RunStatus.RUNNING):
                self._storage.update_run(
                    run.id,
                    status=RunStatus.FAILED,
                    error_message="run interrupted (stale after process restart)",
                    finished=True,
                )

    def _has_active_run(self) -> bool:
        for run in self._storage.list_runs(limit=MAX_RUNS):
            if run.status in (RunStatus.QUEUED, RunStatus.RUNNING):
                return True
        return False

    def _execute_run(
        self,
        run_id: str,
        branch: str,
        suite_id: str,
        check: str | None,
        *,
        changed_only: bool,
        since: str | None,
    ) -> None:
        try:
            self._perform_run(
                run_id,
                branch,
                suite_id,
                check,
                changed_only=changed_only,
                since=since,
            )
        except Exception as exc:  # ruff: ignore[blind-except] — persist any run failure
            message = str(exc) or exc.__class__.__name__
            self._persist_failure(run_id, message)
        finally:
            self._finish_run(run_id)

    def _perform_run(
        self,
        run_id: str,
        branch: str,
        suite_id: str,
        check: str | None,
        *,
        changed_only: bool,
        since: str | None,
    ) -> None:
        worktree = self._resolve_worktree(branch)
        self._storage.update_run(run_id, status=RunStatus.RUNNING, worktree_path=str(worktree))
        install_suite(worktree, suite_id, self._app._catalog_for(worktree))

        cancel_event = self._cancel_events.setdefault(run_id, threading.Event())
        on_progress = partial(self._handle_run_progress, self._storage, run_id, worktree)

        command = RunCommand(
            project_root=worktree,
            suite=suite_id,
            check=check,
            quiet=True,
            changed_only=changed_only,
            since=since,
        )
        exit_code, report = self._app.run_suite(
            command,
            RunMode.CHECK,
            run_id=run_id,
            on_progress=on_progress,
            write_reports=True,
            emit_failure_output=False,
            should_cancel=cancel_event.is_set,
        )
        summary = ingest_run_report(self._storage, run_id, report, worktree)
        if cancel_event.is_set():
            status = RunStatus.CANCELLED
            self._storage.update_run(
                run_id,
                status=status,
                finished=True,
                summary=summary,
                error_message="cancelled",
            )
        else:
            status = RunStatus.SUCCEEDED if exit_code == 0 else RunStatus.FAILED
            self._storage.update_run(run_id, status=status, finished=True, summary=summary)
        with suppress(FileNotFoundError, OSError):
            from shipgate.runtime.report_store import ReportStore

            ReportStore(worktree).merge_metadata(run_id, {"branch": branch})
        self._storage.prune_old_runs(keep=MAX_RUNS)

    def _resolve_worktree(self, branch: str) -> Path:
        try:
            return WorktreeManager(self._primary_root).resolve_run_root(branch)
        except WorktreeError as exc:
            raise OrchestratorError(f"worktree failed: {exc}") from exc

    def _persist_failure(self, run_id: str, message: str) -> None:
        try:
            self._storage.update_run(
                run_id, status=RunStatus.FAILED, error_message=message, finished=True
            )
        except Exception as update_exc:
            update_message = str(update_exc) or update_exc.__class__.__name__
            raise OrchestratorError(
                f"{message}; failed to persist status: {update_message}"
            ) from update_exc

    @staticmethod
    def _handle_run_progress(
        storage: Storage,
        run_id: str,
        worktree: Path,
        progress: RunProgress,
    ) -> None:
        storage.update_run(
            run_id,
            current_check_id=progress.current_check_id or None,
            checks_completed=progress.checks_completed,
            checks_total=progress.checks_total,
        )
        if progress.completed_check is not None:
            summary = ingest_check_into_storage(storage, run_id, progress.completed_check, worktree)
            storage.update_run(run_id, summary=summary)

    def _finish_run(self, run_id: str) -> None:
        with self._lock:
            if self._active_run_id == run_id:
                self._active_run_id = None
            self._cancel_events.pop(run_id, None)
            self._done.set()
