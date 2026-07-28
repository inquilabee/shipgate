"""Native rule for ``guard``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import (
    IfRewriteRule,
    if_else_blocks,
    negated_expr,
    single_terminal_stmt,
)

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class GuardRule(IfRewriteRule):
    rule_id = "guard"
    summary = "Guard"
    message = "Use a guard clause for the terminal else branch"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        blocks = if_else_blocks(node)
        if blocks is None or not isinstance(node, cst.If):
            return None
        body, else_body = blocks
        if single_terminal_stmt(else_body) is None:
            return None
        return [
            node.with_changes(
                test=negated_expr(node.test),
                body=else_body,
                orelse=None,
            ),
            *list(body.body),
        ]
