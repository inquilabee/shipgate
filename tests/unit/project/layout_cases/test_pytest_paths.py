from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_detect_pytest_testpaths_beats_basename(tmp_path: Path) -> None:
    write_file(tmp_path / "pyproject.toml", '[tool.pytest.ini_options]\ntestpaths = ["spec"]\n')
    write_file(tmp_path / "pkg" / "__init__.py")
    write_file(tmp_path / "pkg" / "mod.py", "x = 1\n")
    write_file(tmp_path / "spec" / "test_mod.py", "def test_mod():\n    assert True\n")
    layout = detect_layout(tmp_path)
    assert "pkg" in layout.python_dirs
    assert layout.test_dirs == ("spec",)
