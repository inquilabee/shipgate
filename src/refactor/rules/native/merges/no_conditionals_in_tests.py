"""Native rule for ``no-conditionals-in-tests``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import is_test_path
from refactor.rules.native.stmt_base import IfRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement
    from refactor.protocol import Hit


class NoConditionalsInTestsRule(IfRewriteRule):
    rule_id = "no-conditionals-in-tests"
    summary = "No conditionals in tests"
    message = "Avoid conditionals in tests"

    def detect(self, source: str, path: str) -> list[Hit]:
        return super().detect(source, path) if is_test_path(path) else []

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
        body = list(node.body.body)
        if isinstance(node.orelse, cst.Else):
            body.extend(cast("list[cst.BaseStatement]", list(node.orelse.body.body)))
        return body
