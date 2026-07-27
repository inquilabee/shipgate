"""Replace min/max ternaries with ``min()`` / ``max()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class MinMaxIdentityRule:
    rule_id = "min-max-identity"
    kind = RuleKind.REFACTOR
    summary = "Replace `x if x < y else y` with `min(x, y)`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = MinMaxIdentityRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_IfExp(self, node: cst.IfExp) -> bool:  # ruff:ignore[invalid-function-name]
            match = MinMaxIdentityRule.match_min_max(node)
            if match is None:
                return True
            func_name, left, right = match
            self.hits.append(MinMaxIdentityRule.hit_for(node, func_name, left, right, self.path))
            return True

    @staticmethod
    def match_min_max(
        node: cst.IfExp,
    ) -> tuple[str, cst.BaseExpression, cst.BaseExpression] | None:
        if not isinstance(node.test, cst.Comparison):
            return None
        if len(node.test.comparisons) != 1:
            return None
        operator = node.test.comparisons[0].operator
        comparator = node.test.comparisons[0].comparator
        if not node.test.left.deep_equals(node.body):
            return None
        if not comparator.deep_equals(node.orelse):
            return None
        if isinstance(operator, cst.LessThan):
            return "min", node.body, node.orelse
        if isinstance(operator, cst.GreaterThan):
            return "max", node.body, node.orelse
        return None

    @staticmethod
    def hit_for(
        node: cst.IfExp,
        func_name: str,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after_expr = cst.Call(
            func=cst.Name(func_name),
            args=[cst.Arg(value=left), cst.Arg(value=right)],
        )
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=after_expr)])]
        ).code.strip()
        return Hit(
            rule_id="min-max-identity",
            message=f"Prefer `{func_name}()` over conditional",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
