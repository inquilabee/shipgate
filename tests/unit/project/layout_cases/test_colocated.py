from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_colocated_tests_keep_package_as_python(tmp_path: Path) -> None:
    write_file(tmp_path / "mypkg" / "__init__.py")
    write_file(tmp_path / "mypkg" / "service.py", "def f():\n    return 1\n")
    write_file(tmp_path / "mypkg" / "test_service.py", "def test_f():\n    assert True\n")
    layout = detect_layout(tmp_path)
    assert layout.python_dirs == ("mypkg",)
    assert "mypkg" not in layout.test_dirs
