"""Replace ``x == True`` / ``x == False`` with ``x`` / ``not x``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class SimplifyBooleanComparisonRule:
    rule_id = "simplify-boolean-comparison"
    kind = RuleKind.REFACTOR
    summary = "Replace `x == True` with `x`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = SimplifyBooleanComparisonRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

        def visit_Comparison(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.Comparison,
        ) -> bool:
            replacement = SimplifyBooleanComparisonRule.match_boolean_compare(node)
            if replacement is None:
                return True
            self.hits.append(SimplifyBooleanComparisonRule.hit_for(node, replacement, self.path))
            return True

    @staticmethod
    def is_true(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Name) and node.value == "True"

    @staticmethod
    def is_false(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Name) and node.value == "False"

    @staticmethod
    def match_boolean_compare(node: cst.Comparison) -> cst.BaseExpression | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        if SimplifyBooleanComparisonRule.is_true(comparison.comparator):
            return node.left
        if SimplifyBooleanComparisonRule.is_false(comparison.comparator):
            return cst.UnaryOperation(operator=cst.Not(), expression=node.left)
        return None

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        replacement: cst.BaseExpression,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=replacement)])]
        ).code.strip()
        return Hit(
            rule_id="simplify-boolean-comparison",
            message="Simplify boolean comparison",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
