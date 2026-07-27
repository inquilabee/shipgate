from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_gitignore_skips_venv_python(tmp_path: Path) -> None:
    write_file(tmp_path / ".gitignore", ".venv/\n")
    write_file(tmp_path / "src" / "demo" / "__init__.py")
    write_file(tmp_path / ".venv" / "lib" / "site.py", "x = 1\n")
    assert detect_layout(tmp_path).python_dirs == ("src",)
