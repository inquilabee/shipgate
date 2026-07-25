"""Shared subprocess runner for production command execution."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float | None = None,
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
    stdin_input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` with list-form exec (never ``shell=True``).

    Defaults match the common ShipGate pattern: capture stdout/stderr as text,
    do not raise on non-zero exit (``check=False``), no timeout unless set.
    """
    if isinstance(argv, (str, bytes)):
        raise TypeError("argv must be a sequence of strings, not a string")
    return subprocess.run(  # ruff:ignore[subprocess-without-shell-equals-true]
        list(argv),
        cwd=cwd,
        env=None if env is None else dict(env),
        timeout=timeout,
        check=check,
        capture_output=capture_output,
        text=text,
        input=stdin_input,
        shell=False,
    )
