"""Baseline comparison."""

from __future__ import annotations

import json
from pathlib import Path

from shipgate.domain.reports import RunReport


def baseline_path(project_root: Path) -> Path:
    return project_root / ".shipgate" / "baseline.json"


def save_baseline(project_root: Path, report: RunReport) -> Path:
    path = baseline_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_baseline(project_root: Path) -> RunReport | None:
    path = baseline_path(project_root)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunReport.from_dict(data)
