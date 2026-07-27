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
        if not isinstance(node, cst.FunctionDef) or not isinstance(node.body, cst.IndentedBlock):
            return None
        if len(node.body.body) < 3:
            return None
        return node.with_changes(
            body=node.body.with_changes(
                body=[
                    cst.SimpleStatementLine(
                        body=[cst.Expr(value=cst.Call(func=cst.Name("_extracted_method")))],
                    ),
                    *node.body.body[2:],
                ],
            ),
        )
