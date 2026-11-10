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


class CheckTimeoutError(ExecutionError):
    """One tool outlived its time limit; carries whatever it had printed."""

    def __init__(
        self, argv: tuple[str, ...], timeout_seconds: int, *, stdout: str = "", stderr: str = ""
    ) -> None:
        super().__init__(f"command timed out after {timeout_seconds}s: {' '.join(argv)}")
        self.timeout_seconds = timeout_seconds
        self.stdout = stdout
        self.stderr = stderr


class Executor:
    def __init__(self, timeout_seconds: int = 600) -> None:
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def captured_text(value: str | bytes | None) -> str:
        return value.decode(errors="replace") if isinstance(value, bytes) else value or ""

    def run(
        self,
        argv: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> ProcessResult:
        """Run *argv*; *timeout_seconds* overrides the executor's default for this call."""
        limit = timeout_seconds or self.timeout_seconds
        start = time.monotonic()
        try:
            completed = run_command(argv, cwd=cwd, env=env, timeout=limit)
        except subprocess.TimeoutExpired as exc:
            raise CheckTimeoutError(
                argv,
                limit,
                stdout=self.captured_text(exc.stdout),
                stderr=self.captured_text(exc.stderr),
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
