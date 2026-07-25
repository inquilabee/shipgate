"""Deterministic orchestrator for Playwright UI tests (no real suite runs)."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from shipgate.frontend.domain.models import RunRecord, RunStatus
from shipgate.frontend.domain.requirements import is_acknowledged
from shipgate.frontend.services.orchestrator import OrchestratorError
from shipgate.frontend.storage.base import MAX_RUNS, Storage
from shipgate.runtime.reports import generate_run_id


class FakeOrchestrator:
    """Mirrors RunOrchestrator start/cancel surface with timed progress updates."""

    def __init__(
        self,
        primary_root: Path,
        storage: Storage,
        *,
        step_delay: float = 0.15,
        auto_complete: bool = True,
    ) -> None:
        self._primary_root = Path(primary_root).resolve()
        self._storage = storage
        self._step_delay = step_delay
        self._auto_complete = auto_complete
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
        del check, changed_only, since
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
                args=(run.id,),
                daemon=True,
                name=f"fake-run-{run.id}",
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

    def _execute_run(self, run_id: str) -> None:
        try:
            self._perform_run(run_id)
        finally:
            with self._lock:
                if self._active_run_id == run_id:
                    self._active_run_id = None
                self._cancel_events.pop(run_id, None)
                self._done.set()

    def _perform_run(self, run_id: str) -> None:
        cancel = self._cancel_events.setdefault(run_id, threading.Event())
        self._storage.update_run(
            run_id,
            status=RunStatus.RUNNING,
            checks_completed=0,
            checks_total=0,
            worktree_path=str(self._primary_root),
        )
        time.sleep(self._step_delay)
        if cancel.is_set():
            self._storage.update_run(
                run_id,
                status=RunStatus.CANCELLED,
                finished=True,
                error_message="cancelled",
            )
            return
        self._storage.update_run(
            run_id,
            checks_completed=0,
            checks_total=3,
            current_check_id="ruff.lint",
        )
        for completed, check_id in (
            (1, "bandit.scan"),
            (2, "gitleaks.scan"),
            (3, None),
        ):
            time.sleep(self._step_delay)
            if cancel.is_set():
                self._storage.update_run(
                    run_id,
                    status=RunStatus.CANCELLED,
                    finished=True,
                    error_message="cancelled",
                    checks_completed=completed - 1,
                )
                return
            self._storage.update_run(
                run_id,
                checks_completed=completed,
                checks_total=3,
                current_check_id=check_id,
            )
        if self._auto_complete:
            if cancel.is_set():
                self._storage.update_run(
                    run_id,
                    status=RunStatus.CANCELLED,
                    finished=True,
                    error_message="cancelled",
                )
            else:
                self._storage.update_run(run_id, status=RunStatus.SUCCEEDED, finished=True)
        else:
            # Hold RUNNING until cancel (cancel scenario).
            while not cancel.wait(timeout=0.05):
                pass
            self._storage.update_run(
                run_id,
                status=RunStatus.CANCELLED,
                finished=True,
                error_message="cancelled",
            )
