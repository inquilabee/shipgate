from __future__ import annotations

from shipgate.project.layout import ProjectLayout
from shipgate.project.scope_defaults import default_scopes


def test_default_scopes_multiple_roots_use_include() -> None:
    layout = ProjectLayout(
        python_dirs=("pkg_a", "pkg_b"),
        test_dirs=("tests", "integration"),
        docs_dirs=("docs",),
    )
    scopes = default_scopes(layout)
    assert scopes["python-src"] == {"target": ".", "include": ["pkg_a", "pkg_b"]}
    assert scopes["docs"] == {"target": "docs"}
