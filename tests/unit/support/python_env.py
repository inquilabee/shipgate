"""Shared helpers for unit tests."""

from __future__ import annotations

import sys


class PythonEnvFixture:
    @staticmethod
    def write_venv(path) -> None:
        if sys.platform == "win32":
            scripts = path / "Scripts"
            scripts.mkdir(parents=True)
            (scripts / "python.exe").write_text("", encoding="utf-8")
        else:
            bindir = path / "bin"
            bindir.mkdir(parents=True)
            (bindir / "python").write_text("", encoding="utf-8")
