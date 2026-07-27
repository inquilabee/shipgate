"""Shared helpers for unit tests."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class PythonEnvFixture:
    """Create a minimal fake venv tree for resolver tests."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self) -> None:
        if sys.platform == "win32":
            scripts = self.path / "Scripts"
            scripts.mkdir(parents=True)
            (scripts / "python.exe").write_text("", encoding="utf-8")
            return
        bindir = self.path / "bin"
        bindir.mkdir(parents=True)
        (bindir / "python").write_text("", encoding="utf-8")
