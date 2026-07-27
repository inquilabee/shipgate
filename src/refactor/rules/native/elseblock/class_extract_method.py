"""Native rule for ``class-extract-method``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ClassRewriteRule


class ClassExtractMethodRule(ClassRewriteRule):
    rule_id = "class-extract-method"
    summary = "Class extract method"
    message = "Extract repeated class method body statements into a helper"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        _ = cls, node
        return None
