"""Replace ``for x in ys: yield x`` with ``yield from ys``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

BodyStatement = cst.SimpleStatementLine | cst.BaseCompoundStatement

if TYPE_CHECKING:
    from collections.abc import Sequence


class YieldFromRule:
    rule_id = "yield-from"
    kind = RuleKind.REFACTOR
    summary = "Replace `for x in ys: yield x` with `yield from ys`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = YieldFromRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.IndentedBlock,
        ) -> bool:
            YieldFromRule.check_body(node.body, self.hits, self.path)
            return True

    @staticmethod
    def check_body(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        if len(body) != 1:
            return
        match = YieldFromRule.match_yield_loop(body[0])
        if match is None:
            return
        for_stmt, iterable = match
        hits.append(YieldFromRule.hit_for(for_stmt, iterable, path))

    @staticmethod
    def match_yield_loop(
        stmt: cst.BaseStatement,
    ) -> tuple[cst.For, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.For) or stmt.orelse:
            return None
        if not isinstance(stmt.target, cst.Name):
            return None
        if not isinstance(stmt.body, cst.IndentedBlock):
            return None
        yielded = YieldFromRule.yielded_name(stmt.body)
        if yielded is None or yielded != stmt.target.value:
            return None
        return stmt, stmt.iter

    @staticmethod
    def yielded_name(body: cst.IndentedBlock) -> str | None:
        if len(body.body) != 1:
            return None
        inner = body.body[0]
        if not isinstance(inner, cst.SimpleStatementLine) or len(inner.body) != 1:
            return None
        expr = inner.body[0]
        if not isinstance(expr, cst.Expr) or not isinstance(expr.value, cst.Yield):
            return None
        if expr.value.value is None:
            return None
        if not isinstance(expr.value.value, cst.Name):
            return None
        return expr.value.value.value

    @staticmethod
    def hit_for(for_stmt: cst.For, iterable: cst.BaseExpression, path: str) -> Hit:
        before = cst.Module(body=[cast("BodyStatement", for_stmt)]).code.strip()
        yield_from = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.Yield(value=cst.From(item=iterable)))]
        )
        after = cst.Module(body=[yield_from]).code.strip()
        return Hit(
            rule_id="yield-from",
            message="Prefer `yield from` over yield-in-loop",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
