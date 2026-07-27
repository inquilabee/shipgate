"""Native rule for ``remove-redundant-except-handler``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import TryRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class RemoveRedundantExceptHandlerRule(TryRewriteRule):
    rule_id = "remove-redundant-except-handler"
    summary = "Remove redundant except handler"
    message = "Remove an except handler that only re-raises"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | list[BodyStatement] | None:
        if not isinstance(node, cst.Try):
            return None
        redundant = RemoveRedundantExceptHandlerRule.bare_reraise_handler(node.handlers)
        if redundant is None:
            return None
        handlers = [handler for handler in node.handlers if handler is not redundant]
        if handlers:
            return node.with_changes(handlers=handlers)
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        return [cast("BodyStatement", stmt) for stmt in node.body.body]

    @staticmethod
    def bare_reraise_handler(
        handlers: Sequence[cst.ExceptHandler],
    ) -> cst.ExceptHandler | None:
        redundant = [
            handler
            for handler in handlers
            if RemoveRedundantExceptHandlerRule.is_bare_reraise_handler(handler)
        ]
        if len(redundant) != 1:
            return None
        return redundant[0]

    @staticmethod
    def is_bare_reraise_handler(handler: cst.ExceptHandler) -> bool:
        if not isinstance(handler.body, cst.IndentedBlock):
            return False
        stmt = single_small_stmt(handler.body)
        return isinstance(stmt, cst.Raise) and stmt.exc is None
