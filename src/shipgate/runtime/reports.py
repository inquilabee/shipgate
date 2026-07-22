"""Report writing and run ID generation."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.paths import failure_report_dir, raw_reports_dir
from shipgate.runtime.core.json_io import dumps_indented

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.reports import RunReport


def generate_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(3)
    return f"{timestamp}-{suffix}"


def write_run_report(project_root: Path, report: RunReport) -> Path:
    out_dir = failure_report_dir(project_root, report.run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(dumps_indented(report.to_dict()), encoding="utf-8")
    return path


def write_raw_output(
    project_root: Path,
    run_id: str,
    check_id: str,
    *,
    stdout: str = "",
    stderr: str = "",
    tool_output: str | None = None,
) -> tuple[Path, Path, Path | None]:
    base = raw_reports_dir(project_root, run_id) / check_id
    base.mkdir(parents=True, exist_ok=True)
    stdout_path = base / "stdout.txt"
    stderr_path = base / "stderr.txt"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    tool_path = None
    if tool_output is not None:
        tool_path = base / "tool-output.json"
        tool_path.write_text(tool_output, encoding="utf-8")
    return stdout_path, stderr_path, tool_path
