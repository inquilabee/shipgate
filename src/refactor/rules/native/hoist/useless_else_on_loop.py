"""Native rule for ``useless-else-on-loop``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class UselessElseOnLoopRule(ForRewriteRule):
    rule_id = "useless-else-on-loop"
    summary = "Useless else on loop"
    message = "Remove loop else by placing its body after the loop"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        return (
            None
            if not isinstance(node, cst.For) or node.orelse is None
            else cast(
                "list[BodyStatement]",
                [
                    node.with_changes(orelse=None),
                    *list(node.orelse.body.body),
                ],
            )
        )
