"""Native rule for ``no-loop-in-tests``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import is_test_path
from refactor.rules.native.stmt_base import ForRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement
    from refactor.protocol import Hit


class NoLoopInTestsRule(ForRewriteRule):
    rule_id = "no-loop-in-tests"
    summary = "No loop in tests"
    message = "Avoid loops in tests"

    def detect(self, source: str, path: str) -> list[Hit]:
        return super().detect(source, path) if is_test_path(path) else []

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> Sequence[BodyStatement] | None:
        if not isinstance(node, cst.For) or not isinstance(node.body, cst.IndentedBlock):
            return None
        return [cast("BodyStatement", stmt) for stmt in node.body.body]
