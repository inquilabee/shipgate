"""Report history storage and index."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.core.json_io import dumps_indented
from shipgate.domain.reports import RunReport
from shipgate.paths import PROJECT_REPORTS_DIR, PROJECT_REPORTS_FAILURES_DIR

if TYPE_CHECKING:
    from pathlib import Path


class ReportStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.root = project_root / PROJECT_REPORTS_DIR
        self.runs_dir = self.root / "runs"
        self.index_path = self.root / "index.json"

    def save(self, report: RunReport, *, metadata: dict | None = None) -> Path:
        run_dir = self.runs_dir / report.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "report.json"
        report_path.write_text(
            dumps_indented(report.to_dict(), trailing_newline=False),
            encoding="utf-8",
        )
        meta = {
            "run_id": report.run_id,
            "suite": report.suite,
            "mode": report.mode,
            "status": report.status,
            "finding_count": sum(len(c.findings) for c in report.reports),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if metadata:
            meta.update(metadata)
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
        return finalized

    def _write_failure_report(self, report: RunReport) -> Path:
        out_dir = self.project_root / PROJECT_REPORTS_FAILURES_DIR / report.run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "report.json"
        path.write_text(dumps_indented(report.to_dict()), encoding="utf-8")
        return path

    def _update_index(self, entry: dict) -> None:
        index = self._load_index()
        index = [e for e in index if e.get("run_id") != entry["run_id"]]
        index.insert(0, entry)
        index = index[:100]
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(dumps_indented(index, trailing_newline=False), encoding="utf-8")
        tmp.replace(self.index_path)

    def _load_index(self) -> list[dict]:
        if not self.index_path.is_file():
            return []
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def list_runs(self) -> list[dict]:
        return self._load_index()

    def load(self, run_id: str) -> RunReport:
        path = self.runs_dir / run_id / "report.json"
        if not path.is_file():
            failures = self.root / "failures" / run_id / "report.json"
            if failures.is_file():
                path = failures
            else:
                raise FileNotFoundError(f"run not found: {run_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunReport.from_dict(data)
