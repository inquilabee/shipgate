"""Native rule for ``extract-method``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import FunctionRewriteRule


class ExtractMethodRule(FunctionRewriteRule):
    rule_id = "extract-method"
    summary = "Extract method"
    message = "Extract the leading function body statements into a helper"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        _ = cls, node
        return None
