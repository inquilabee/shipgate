"""Replace ``== None`` / ``!= None`` with ``is None`` / ``is not None``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    apply_with_transformer,
    detect_with_visitor,
    expr_replacement_hit,
    is_none_name,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class NoneCompareRule:
    rule_id = "none-compare"
    kind = RuleKind.REFACTOR
    summary = "Replace `== None` with `is None`"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, NoneCompareRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, NoneCompareRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Comparison(
            self,
            original_node: cst.Comparison,
            updated_node: cst.Comparison,
        ) -> cst.BaseExpression:
            _ = self, original_node
            replacement = NoneCompareRule.match_none_compare(updated_node)
            return updated_node if replacement is None else replacement

    class Finder(HitCollector):
        def visit_Comparison(
            self,
            node: cst.Comparison,
        ) -> bool:
            match = NoneCompareRule.match_none_compare(node)
            if match is None:
                return True
            self.hits.append(NoneCompareRule.hit_for(node, match, self.path))
            return True

    @staticmethod
    def match_none_compare(node: cst.Comparison) -> cst.Comparison | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        operator = comparison.operator
        comparator = comparison.comparator
        return (
            cst.Comparison(
                left=node.left,
                comparisons=[cst.ComparisonTarget(operator=cst.Is(), comparator=comparator)],
            )
            if isinstance(operator, cst.Equal) and is_none_name(comparator)
            else (
                cst.Comparison(
                    left=node.left,
                    comparisons=[cst.ComparisonTarget(operator=cst.IsNot(), comparator=comparator)],
                )
                if isinstance(operator, cst.NotEqual) and is_none_name(comparator)
                else None
            )
        )

    @staticmethod
    def hit_message(node: cst.Comparison) -> str:
        return (
            "Prefer `is not None` over `!= None`"
            if len(node.comparisons) == 1 and isinstance(node.comparisons[0].operator, cst.NotEqual)
            else "Prefer `is None` over `== None`"
        )

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        replacement: cst.Comparison,
        path: str,
    ) -> Hit:
        return expr_replacement_hit(
            rule_id="none-compare",
            message=NoneCompareRule.hit_message(node),
            path=path,
            before_expr=node,
            after_expr=replacement,
        )
