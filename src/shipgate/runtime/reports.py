"""Report writing and run ID generation."""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.errors import ExecutionError
from shipgate.paths import PROJECT_REPORTS_RAW_DIR

if TYPE_CHECKING:
    from pathlib import Path

RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def generate_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(3)
    return f"{timestamp}-{suffix}"


def validate_run_id(run_id: str) -> str:
    if not run_id or not RUN_ID_PATTERN.fullmatch(run_id) or ".." in run_id:
        raise ExecutionError(
            f"invalid run id {run_id!r}",
            hint="run ids must be alphanumeric with optional . _ -",
        )
    return run_id


def write_raw_output(
    project_root: Path,
    run_id: str,
    check_id: str,
    *,
    stdout: str = "",
    stderr: str = "",
    tool_output: str | None = None,
) -> tuple[Path, Path, Path | None]:
    safe_run_id = validate_run_id(run_id)
    base = project_root / PROJECT_REPORTS_RAW_DIR / safe_run_id / check_id
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
