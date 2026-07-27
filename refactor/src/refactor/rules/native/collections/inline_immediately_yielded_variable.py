"""Native rule for ``inline-immediately-yielded-variable``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.rules.native.stmt_base import BodySequenceRewriteRule

if TYPE_CHECKING:
    from collections.abc import Sequence


class InlineImmediatelyYieldedVariableRule(BodySequenceRewriteRule):
    rule_id = "inline-immediately-yielded-variable"
    summary = "Inline immediately yielded variable"
    message = "Inline a variable that is immediately yielded"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, assign_stmt in enumerate(body[:-1]):
            yield_stmt = body[index + 1]
            assign = cls.single_assign(assign_stmt)
            yielded = cls.single_yield(yield_stmt)
            if assign is None or yielded is None:
                continue
            target, value = assign
            if not isinstance(yielded.value, cst.Name) or yielded.value.value != target:
                continue
            return (
                [assign_stmt, yield_stmt],
                [cst.SimpleStatementLine(body=[cst.Expr(value=yielded.with_changes(value=value))])],
            )
        return None

    @staticmethod
    def single_assign(stmt: cst.BaseStatement) -> tuple[str, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        return (target.value, assign.value) if isinstance(target, cst.Name) else None

    @staticmethod
    def single_yield(stmt: cst.BaseStatement) -> cst.Yield | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        small_stmt = stmt.body[0]
        if isinstance(small_stmt, cst.Expr) and isinstance(small_stmt.value, cst.Yield):
            return small_stmt.value
        return None
