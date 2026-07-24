import ast
from pathlib import Path


def test_planning_incremental_does_not_import_runtime():
    src = Path("src/shipgate/planning/utils/incremental.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("shipgate.runtime")
        ):
            raise AssertionError(f"planning imports runtime: {node.module}")


def test_planning_check_resolver_does_not_import_runtime_session():
    src = Path("src/shipgate/planning/check_resolver.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("shipgate.runtime")
        ):
            # TYPE_CHECKING RunContext is still a runtime type — forbid any runtime import.
            raise AssertionError(f"planning imports runtime: {node.module}")
