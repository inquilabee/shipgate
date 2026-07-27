from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_detect_src_layout_and_tests_dir(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "demo" / "__init__.py")
    write_file(tmp_path / "src" / "demo" / "app.py", "x = 1\n")
    write_file(tmp_path / "tests" / "test_app.py", "def test_ok():\n    assert True\n")
    layout = detect_layout(tmp_path)
    assert layout.python_dirs == ("src",)
    assert layout.test_dirs == ("tests",)
