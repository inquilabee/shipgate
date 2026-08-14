from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout
from shipgate.project.layout.packages import detect_importable_packages

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_example_benchmarks_typing_tests_are_not_python_src(tmp_path: Path) -> None:
    write_file(tmp_path / "debug_toolbar" / "__init__.py", "x = 1\n")
    write_file(tmp_path / "debug_toolbar" / "app.py", "x = 1\n")
    write_file(tmp_path / "example" / "__init__.py", "x = 1\n")
    write_file(tmp_path / "example" / "settings.py", "x = 1\n")
    write_file(tmp_path / "benchmarks" / "gzip.py", "x = 1\n")
    write_file(tmp_path / "typing_tests" / "__init__.py")
    write_file(tmp_path / "typing_tests" / "api.py", "x = 1\n")
    write_file(tmp_path / "sphinx" / "conf.py", "project = 'x'\n")
    write_file(tmp_path / "tests" / "test_app.py", "def test_ok():\n    assert True\n")
    layout = detect_layout(tmp_path)
    assert layout.python_dirs == ("debug_toolbar",)
    assert "example" not in layout.python_dirs
    assert "benchmarks" not in layout.python_dirs
    assert "typing_tests" not in layout.python_dirs
    assert "sphinx" not in layout.python_dirs


def test_pep420_namespace_under_src(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "zope" / "interface" / "__init__.py", "x = 1\n")
    write_file(tmp_path / "src" / "zope" / "interface" / "adapter.py", "x = 1\n")
    layout = detect_layout(tmp_path)
    assert layout.python_dirs == ("src",)
    assert detect_importable_packages(tmp_path) == ("zope.interface",)


def test_nested_reports_package_stays_in_src_layout(tmp_path: Path) -> None:
    write_file(tmp_path / "src" / "pkg" / "reports" / "__init__.py", "x = 1\n")
    write_file(tmp_path / "src" / "pkg" / "reports" / "mod.py", "x = 1\n")
    layout = detect_layout(tmp_path)
    assert layout.python_dirs == ("src",)
