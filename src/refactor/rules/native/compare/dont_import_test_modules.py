"""Native rule for ``dont-import-test-modules``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import SimpleStatementLineRewriteRule


class DontImportTestModulesRule(SimpleStatementLineRewriteRule):
    rule_id = "dont-import-test-modules"
    summary = "Dont import test modules"
    message = "Do not import test modules from production code"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        if isinstance(node, cst.Import):
            has_test_module = any(cls.is_test_module(alias.name) for alias in node.names)
            return cst.Pass() if has_test_module else None
        return (
            (cst.Pass() if cls.is_test_module(node.module) else None)
            if isinstance(node, cst.ImportFrom) and node.module is not None
            else None
        )

    @classmethod
    def is_test_module(cls, node: cst.BaseExpression) -> bool:
        return (
            node.value.startswith("test")
            if isinstance(node, cst.Name)
            else (cls.is_test_module(node.value) if isinstance(node, cst.Attribute) else False)
        )
