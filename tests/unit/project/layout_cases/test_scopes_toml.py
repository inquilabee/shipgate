from __future__ import annotations

from shipgate.project.layout import ProjectLayout
from shipgate.project.scope_defaults import render_scopes_toml


def test_render_scopes_toml_contains_named_scopes() -> None:
    layout = ProjectLayout(python_dirs=("src",), test_dirs=(), docs_dirs=("docs",))
    text = render_scopes_toml(layout)
    assert "[tool.shipgate.scopes.python-src]" in text
    assert 'target = "src"' in text
