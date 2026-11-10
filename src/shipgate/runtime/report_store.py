"""Report history storage and index."""

from __future__ import annotations

import itertools
import json
import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.core.json_io import dumps_indented
from shipgate.domain.reports import RunReport
from shipgate.errors import ExecutionError
from shipgate.paths import PROJECT_REPORTS_DIR, PROJECT_REPORTS_FAILURES_DIR
from shipgate.runtime.reports import RUN_ID_PATTERN, validate_run_id

if TYPE_CHECKING:
    from pathlib import Path

REPORT_FILENAME = "report.json"
DEFAULT_KEEP_RUNS = 50


class ReportStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.root = (project_root / PROJECT_REPORTS_DIR).resolve()
        self.runs_dir = self.root / "runs"
        self.index_path = self.root / "index.json"

    def save(self, report: RunReport, *, metadata: dict | None = None) -> Path:
        run_id = validate_run_id(report.run_id)
        run_dir = self._contained_run_dir(self.runs_dir, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / REPORT_FILENAME
        report_path.write_text(
            dumps_indented(report.to_dict(), trailing_newline=False),
            encoding="utf-8",
        )
        meta = {
            "run_id": run_id,
            "suite": report.suite,
            "mode": report.mode,
            "status": report.status,
            "finding_count": sum(len(c.findings) for c in report.reports),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if metadata:
            meta |= metadata
        (run_dir / "metadata.json").write_text(
            dumps_indented(meta, trailing_newline=False),
            encoding="utf-8",
        )
        self._update_index(meta)
        return report_path

    def save_final(self, report: RunReport, *, metadata: dict | None = None) -> RunReport:
        """Persist a completed run; failed runs also write failures/ and report_path."""
        finalized = report
        if report.status == "failed":
            failure_path = self._write_failure_report(report)
            finalized = RunReport(
                run_id=report.run_id,
                suite=report.suite,
                mode=report.mode,
                status=report.status,
                reports=report.reports,
                report_path=str(failure_path.relative_to(self.project_root)),
            )
        self.save(finalized, metadata=metadata)
        self.prune()
        return finalized

    def _write_failure_report(self, report: RunReport) -> Path:
        run_id = validate_run_id(report.run_id)
        failures_root = (self.project_root / PROJECT_REPORTS_FAILURES_DIR).resolve()
        out_dir = self._contained_run_dir(failures_root, run_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / REPORT_FILENAME
        path.write_text(dumps_indented(report.to_dict()), encoding="utf-8")
        return path

    def _update_index(self, entry: dict) -> None:
        index = self._load_index()
        index = [e for e in index if e.get("run_id") != entry["run_id"]]
        index.insert(0, entry)
        self._write_index(index[:100])

    def _write_index(self, index: list[dict]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(dumps_indented(index, trailing_newline=False), encoding="utf-8")
        tmp.replace(self.index_path)

    def prune(self, keep: int = DEFAULT_KEEP_RUNS) -> int:
        """Keep the newest *keep* runs; drop older ones from runs/, raw/ and failures/.

        The index is trimmed to the survivors so the report UI never links to a
        run that is gone. Returns how many runs were removed.
        """
        if keep < 1:
            raise ExecutionError("keep must be at least 1", hint="use a positive run count")
        newest_first = self._run_ids_newest_first()
        for run_id, base in itertools.product(newest_first[keep:], self.run_roots()):
            shutil.rmtree(self._contained_run_dir(base, run_id), ignore_errors=True)
        survivors = set(newest_first[:keep])
        index = self._load_index()
        if any(entry.get("run_id") not in survivors for entry in index):
            self._write_index([e for e in index if e.get("run_id") in survivors])
        return max(len(newest_first) - keep, 0)

    def run_roots(self) -> tuple[Path, ...]:
        return (self.runs_dir, self.root / "raw", self.root / "failures")

    def _run_ids_newest_first(self) -> list[str]:
        """Run ids found on disk, by most recent activity (other dirs are left alone)."""
        latest: dict[str, float] = {}
        for base in self.run_roots():
            children = base.iterdir() if base.is_dir() else ()
            for child in children:
                if child.is_dir() and RUN_ID_PATTERN.fullmatch(child.name):
                    latest[child.name] = max(latest.get(child.name, 0.0), child.stat().st_mtime)
        return sorted(latest, key=lambda run_id: (latest[run_id], run_id), reverse=True)

    def _load_index(self) -> list[dict]:
        return (
            json.loads(self.index_path.read_text(encoding="utf-8"))
            if self.index_path.is_file()
            else []
        )

    def list_runs(self) -> list[dict]:
        return self._load_index()

    def merge_metadata(self, run_id: str, metadata: dict) -> None:
        """Merge keys into metadata.json and refresh the index entry for a saved run."""
        safe_run_id = validate_run_id(run_id)
        run_dir = self._contained_run_dir(self.runs_dir, safe_run_id)
        meta_path = run_dir / "metadata.json"
        meta: dict = {}
        if meta_path.is_file():
            meta = dict(json.loads(meta_path.read_text(encoding="utf-8")))
        elif not (run_dir / REPORT_FILENAME).is_file():
            raise FileNotFoundError(f"run not found: {safe_run_id}")
        meta |= metadata
        meta.setdefault("run_id", safe_run_id)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            dumps_indented(meta, trailing_newline=False),
            encoding="utf-8",
        )
        self._update_index(meta)

    def load(self, run_id: str) -> RunReport:
        safe_run_id = validate_run_id(run_id)
        path = self._contained_run_dir(self.runs_dir, safe_run_id) / REPORT_FILENAME
        if not path.is_file():
            failures_root = (self.root / "failures").resolve()
            failures = self._contained_run_dir(failures_root, safe_run_id) / REPORT_FILENAME
            if not failures.is_file():
                raise FileNotFoundError(f"run not found: {safe_run_id}")
            path = failures
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunReport.from_dict(data)

    @staticmethod
    def _contained_run_dir(root: Path, run_id: str) -> Path:
        root_resolved = root.resolve()
        candidate = (root_resolved / run_id).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError as exc:
            raise ExecutionError(
                f"run id escapes reports directory: {run_id!r}",
                path=str(candidate),
            ) from exc
        return candidate
