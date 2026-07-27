"""Replace ``x == True`` / ``x == False`` with ``x`` / ``not x``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    detect_with_visitor,
    expr_replacement_hit,
    is_false,
    is_true,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class SimplifyBooleanComparisonRule:
    rule_id = "simplify-boolean-comparison"
    kind = RuleKind.REFACTOR
    summary = "Replace `x == True` with `x`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, SimplifyBooleanComparisonRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
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
    def match_boolean_compare(node: cst.Comparison) -> cst.BaseExpression | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        if is_true(comparison.comparator):
            return node.left
        if is_false(comparison.comparator):
            return cst.UnaryOperation(operator=cst.Not(), expression=node.left)
        return None

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        replacement: cst.BaseExpression,
        path: str,
    ) -> Hit:
        return expr_replacement_hit(
            rule_id="simplify-boolean-comparison",
            message="Simplify boolean comparison",
            path=path,
            before_expr=node,
            after_expr=replacement,
        )
