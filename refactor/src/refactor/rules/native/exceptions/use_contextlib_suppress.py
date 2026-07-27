"""Native rule for ``use-contextlib-suppress``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import TryRewriteRule


class UseContextlibSuppressRule(TryRewriteRule):
    rule_id = "use-contextlib-suppress"
    summary = "Use contextlib suppress"
    message = "Use contextlib.suppress for ignored exceptions"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.Try) or len(node.handlers) != 1:
            return None
        if node.orelse is not None or node.finalbody is not None:
            return None
        handler = node.handlers[0]
        if not isinstance(handler, cst.ExceptHandler) or handler.type is None:
            return None
        if not isinstance(handler.body, cst.IndentedBlock):
            return None
        if not isinstance(single_small_stmt(handler.body), cst.Pass):
            return None
        return cst.With(
            items=[
                cst.WithItem(
                    item=cst.Call(
                        func=cst.Name("suppress"),
                        args=[cst.Arg(value=handler.type)],
                    ),
                ),
            ],
            body=node.body,
        )
