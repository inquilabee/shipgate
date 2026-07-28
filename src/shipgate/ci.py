"""CI integration helpers."""

from __future__ import annotations

import os
from pathlib import Path


def is_ci_environment() -> bool:
    return os.environ.get("CI", "").lower() in {"1", "true", "yes"} or (
        os.environ.get("GITHUB_ACTIONS") is not None
    )


def apply_ci_defaults(error_format: str | None) -> str:
    return error_format or ("github" if is_ci_environment() else "compact")


def write_github_step_summary(message: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    path = Path(summary_path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(message)
        if not message.endswith("\n"):
            handle.write("\n")
