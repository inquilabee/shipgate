"""Native rule for ``hoist-statement-from-loop``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class HoistStatementFromLoopRule(ForRewriteRule):
    rule_id = "hoist-statement-from-loop"
    summary = "Hoist statement from loop"
    message = "Hoist a trailing statement out of a loop"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        if not isinstance(node, cst.For):
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) < 2:
            return None
        return [
            cast(
                "BodyStatement",
                node.with_changes(
                    body=node.body.with_changes(body=node.body.body[:-1]),
                ),
            ),
            cast("BodyStatement", node.body.body[-1]),
        ]
