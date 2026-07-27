"""Native rule for ``no-conditionals-in-tests``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class NoConditionalsInTestsRule(IfRewriteRule):
    rule_id = "no-conditionals-in-tests"
    summary = "No conditionals in tests"
    message = "Avoid conditionals in tests"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> Sequence[BodyStatement] | None:
        if not isinstance(node, cst.If) or not isinstance(node.body, cst.IndentedBlock):
            return None
        if node.orelse is not None and not isinstance(node.orelse, cst.Else):
            return None
        if isinstance(node.orelse, cst.Else) and not isinstance(
            node.orelse.body,
            cst.IndentedBlock,
        ):
            return None
        body = [cast("BodyStatement", stmt) for stmt in node.body.body]
        if isinstance(node.orelse, cst.Else):
            body.extend(cast("BodyStatement", stmt) for stmt in node.orelse.body.body)
        return body
