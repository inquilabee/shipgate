"""Replace a lone first-element ``for`` loop with ``next(iter(...))``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

BodyStatement = cst.SimpleStatementLine | cst.BaseCompoundStatement

if TYPE_CHECKING:
    from collections.abc import Sequence


class UseNextRule:
    rule_id = "use-next"
    kind = RuleKind.REFACTOR
    summary = "Replace `for x in xs: return x` with `next(iter(xs))`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = UseNextRule.Finder(path=path)
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
            UseNextRule.check_body(node.body, self.hits, self.path)
            return True

    @staticmethod
    def check_body(
        body: Sequence[cst.BaseStatement],
        hits: list[Hit],
        path: str,
    ) -> None:
        if len(body) != 1:
            return
        stmt = body[0]
        match = UseNextRule.match_first_element_for(stmt)
        if match is None:
            return
        for_stmt, iterable = match
        hits.append(UseNextRule.hit_for(for_stmt, iterable, path))

    @staticmethod
    def match_first_element_for(
        stmt: cst.BaseStatement,
    ) -> tuple[cst.For, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.For) or stmt.orelse:
            return None
        if not isinstance(stmt.target, cst.Name):
            return None
        if not isinstance(stmt.body, cst.IndentedBlock):
            return None
        returned = UseNextRule.returned_name(stmt.body)
        if returned is None or returned != stmt.target.value:
            return None
        return stmt, stmt.iter

    @staticmethod
    def returned_name(body: cst.IndentedBlock) -> str | None:
        if len(body.body) != 1:
            return None
        inner = body.body[0]
        if not isinstance(inner, cst.SimpleStatementLine) or len(inner.body) != 1:
            return None
        ret = inner.body[0]
        if not isinstance(ret, cst.Return) or ret.value is None:
            return None
        if not isinstance(ret.value, cst.Name):
            return None
        return ret.value.value

    @staticmethod
    def hit_for(for_stmt: cst.For, iterable: cst.BaseExpression, path: str) -> Hit:
        before = cst.Module(body=[cast("BodyStatement", for_stmt)]).code.strip()
        next_call = cst.Call(
            func=cst.Name("next"),
            args=[cst.Arg(value=cst.Call(func=cst.Name("iter"), args=[cst.Arg(value=iterable)]))],
        )
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Return(value=next_call)])]
        ).code.strip()
        return Hit(
            rule_id="use-next",
            message="Prefer `next(iter(...))` for first element",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
