"""Native rule for ``raise-from-previous-error``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import TryRewriteRule


class RaiseFromPreviousErrorRule(TryRewriteRule):
    rule_id = "raise-from-previous-error"
    summary = "Raise from previous error"
    message = "Raise a new exception from the previous error"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.Try):
            return None
        handlers = [cls.updated_handler(handler) for handler in node.handlers]
        if all(handler is None for handler in handlers):
            return None
        return node.with_changes(
            handlers=[
                updated if updated is not None else original
                for original, updated in zip(node.handlers, handlers, strict=True)
            ],
        )

    @staticmethod
    def updated_handler(handler: cst.ExceptHandler) -> cst.ExceptHandler | None:
        if handler.name is None or not isinstance(handler.name.name, cst.Name):
            return None
        if not isinstance(handler.body, cst.IndentedBlock):
            return None
        stmt = single_small_stmt(handler.body)
        if not isinstance(stmt, cst.Raise) or stmt.exc is None or stmt.cause is not None:
            return None
        return handler.with_changes(
            body=handler.body.with_changes(
                body=[
                    cst.SimpleStatementLine(
                        body=[
                            stmt.with_changes(
                                cause=cst.From(item=cst.Name(handler.name.name.value)),
                            ),
                        ],
                    ),
                ],
            ),
        )
