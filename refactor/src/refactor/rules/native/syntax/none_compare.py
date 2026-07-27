"""Replace ``== None`` / ``!= None`` with ``is None`` / ``is not None``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class NoneCompareRule:
    rule_id = "none-compare"
    kind = RuleKind.REFACTOR
    summary = "Replace `== None` with `is None`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = NoneCompareRule.Finder(path=path)
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
            match = NoneCompareRule.match_none_compare(node)
            if match is None:
                return True
            self.hits.append(NoneCompareRule.hit_for(node, match, self.path))
            return True

    @staticmethod
    def is_none(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Name) and node.value == "None"

    @staticmethod
    def match_none_compare(node: cst.Comparison) -> cst.Comparison | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        operator = comparison.operator
        comparator = comparison.comparator
        if isinstance(operator, cst.Equal) and NoneCompareRule.is_none(comparator):
            return cst.Comparison(
                left=node.left,
                comparisons=[cst.ComparisonTarget(operator=cst.Is(), comparator=comparator)],
            )
        if isinstance(operator, cst.NotEqual) and NoneCompareRule.is_none(comparator):
            return cst.Comparison(
                left=node.left,
                comparisons=[cst.ComparisonTarget(operator=cst.IsNot(), comparator=comparator)],
            )
        return None

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        replacement: cst.Comparison,
        path: str,
    ) -> Hit:
        before = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=node)])]
        ).code.strip()
        after = cst.Module(
            body=[cst.SimpleStatementLine(body=[cst.Expr(value=replacement)])]
        ).code.strip()
        return Hit(
            rule_id="none-compare",
            message="Prefer `is None` over `== None`",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after),
        )
