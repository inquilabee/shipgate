"""Report history storage and index."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.domain.reports import RunReport
from shipgate.paths import reports_root

if TYPE_CHECKING:
    from pathlib import Path


class ReportStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.root = reports_root(project_root)
        self.runs_dir = self.root / "runs"
        self.index_path = self.root / "index.json"

    def save(self, report: RunReport, *, metadata: dict | None = None) -> Path:
        run_dir = self.runs_dir / report.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "report.json"
        report_path.write_text(
            json.dumps(report.to_dict(), indent=2),
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
        (run_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self._update_index(meta)
        return report_path

    def _update_index(self, entry: dict) -> None:
        index = self._load_index()
        index = [e for e in index if e.get("run_id") != entry["run_id"]]
        index.insert(0, entry)
        index = index[:100]
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=2), encoding="utf-8")
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
