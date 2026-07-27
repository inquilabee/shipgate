from __future__ import annotations

from shipgate.project.layout import ProjectLayout
from shipgate.project.scope_defaults import default_scopes


def test_default_scopes_single_python_and_test_roots() -> None:
    scopes = default_scopes(ProjectLayout(python_dirs=("src",), test_dirs=("tests",), docs_dirs=()))
    assert scopes["semgrep"] == {"target": "."}
    assert scopes["python-src"] == {"target": "src"}
    assert scopes["python-test-src"] == {"target": "tests"}
