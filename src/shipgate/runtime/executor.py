"""Process executor."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import ExecutionError

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    cwd: Path
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    output_files: tuple[Path, ...] = ()


class Executor:
    def __init__(self, timeout_seconds: int = 600) -> None:
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        argv: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> ProcessResult:
        start = time.monotonic()
        try:
            completed = run_command(
                argv,
                cwd=cwd,
                env=env,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExecutionError(
                f"command timed out after {self.timeout_seconds}s: {' '.join(argv)}"
            ) from exc
        except OSError as exc:
            raise ExecutionError(f"failed to run command: {exc}") from exc
        duration_ms = int((time.monotonic() - start) * 1000)
        return ProcessResult(
            argv=argv,
            cwd=cwd,
            exit_code=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            duration_ms=duration_ms,
        )
