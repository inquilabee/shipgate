"""Native rule for ``introduce-default-else``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule


class IntroduceDefaultElseRule(IfRewriteRule):
    rule_id = "introduce-default-else"
    summary = "Introduce default else"
    message = "Add an explicit default else branch"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or node.orelse is not None:
            return None
        return node.with_changes(
            orelse=cst.Else(
                body=cst.IndentedBlock(body=[cst.SimpleStatementLine(body=[cst.Pass()])]),
            ),
        )
