from __future__ import annotations

from shipgate.project.layout import ProjectLayout
from shipgate.project.scope_defaults import render_scopes_yaml


def test_render_scopes_yaml_contains_named_scopes() -> None:
    layout = ProjectLayout(python_dirs=("src",), test_dirs=("tests",), docs_dirs=())
    text = render_scopes_yaml(layout)
    assert "python-src:" in text
    assert "target: src" in text
    assert "semgrep:" in text
