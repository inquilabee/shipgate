"""Inline a variable that is assigned and immediately returned."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    IndentedBlockCollector,
    code_for_stmts,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class InlineImmediatelyReturnedVariableRule:
    rule_id = "inline-immediately-returned-variable"
    kind = RuleKind.REFACTOR
    summary = "Inline variable assigned just before return"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, InlineImmediatelyReturnedVariableRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(IndentedBlockCollector):
        def __init__(self, *, path: str) -> None:
            super().__init__(
                path=path,
                checker=InlineImmediatelyReturnedVariableRule.check_body,
            )

    @staticmethod
    def check_body(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        if len(body) < 2:
            return
        assign_stmt = body[-2]
        return_stmt = body[-1]
        match = InlineImmediatelyReturnedVariableRule.match_assign_return(
            assign_stmt,
            return_stmt,
        )
        if match is None:
            return
        name, value = match
        hits.append(
            InlineImmediatelyReturnedVariableRule.hit_for(
                assign_stmt,
                return_stmt,
                name,
                value,
                path,
            )
        )

    @staticmethod
    def match_assign_return(
        assign_stmt: cst.BaseStatement,
        return_stmt: cst.BaseStatement,
    ) -> tuple[str, cst.BaseExpression] | None:
        assign = InlineImmediatelyReturnedVariableRule.extract_assign(assign_stmt)
        if assign is None:
            return None
        target, value = assign
        returned = InlineImmediatelyReturnedVariableRule.extract_returned_name(return_stmt)
        if returned is None or returned != target:
            return None
        return target, value

    @staticmethod
    def extract_assign(
        stmt: cst.BaseStatement,
    ) -> tuple[str, cst.BaseExpression] | None:
        node = InlineImmediatelyReturnedVariableRule.single_assign(stmt)
        if node is None:
            return None
        target = node.targets[0].target
        if not isinstance(target, cst.Name):
            return None
        return target.value, node.value

    @staticmethod
    def extract_returned_name(stmt: cst.BaseStatement) -> str | None:
        node = InlineImmediatelyReturnedVariableRule.single_return(stmt)
        if node is None or node.value is None or not isinstance(node.value, cst.Name):
            return None
        return node.value.value

    @staticmethod
    def single_assign(stmt: cst.BaseStatement) -> cst.Assign | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        node = stmt.body[0]
        if not isinstance(node, cst.Assign) or len(node.targets) != 1:
            return None
        return node

    @staticmethod
    def single_return(stmt: cst.BaseStatement) -> cst.Return | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        node = stmt.body[0]
        if not isinstance(node, cst.Return):
            return None
        return node

    @staticmethod
    def hit_for(
        assign_stmt: cst.BaseStatement,
        return_stmt: cst.BaseStatement,
        name: str,
        value: cst.BaseExpression,
        path: str,
    ) -> Hit:
        _ = name
        return make_hit(
            rule_id="inline-immediately-returned-variable",
            message="Inline immediately returned variable",
            path=path,
            before=code_for_stmts(
                cast("BodyStatement", assign_stmt),
                cast("BodyStatement", return_stmt),
            ),
            after=code_for_stmts(cst.SimpleStatementLine(body=[cst.Return(value=value)])),
        )
