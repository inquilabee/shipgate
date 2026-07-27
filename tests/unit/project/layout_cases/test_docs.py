from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout import detect_layout

from .support import write_file

if TYPE_CHECKING:
    from pathlib import Path


def test_detect_docs_from_mkdocs_and_docs_dir(tmp_path: Path) -> None:
    write_file(tmp_path / "mkdocs.yml", "site_name: Demo\n")
    (tmp_path / "docs").mkdir()
    write_file(tmp_path / "src" / "demo" / "__init__.py")
    layout = detect_layout(tmp_path)
    assert layout.docs_dirs == ("docs",)
    assert layout.python_dirs == ("src",)
