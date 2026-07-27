"""Replace ``== None`` / ``!= None`` with ``is None`` / ``is not None``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    detect_with_visitor,
    expr_replacement_hit,
    is_none_name,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class NoneCompareRule:
    rule_id = "none-compare"
    kind = RuleKind.REFACTOR
    summary = "Replace `== None` with `is None`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, NoneCompareRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
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
    def match_none_compare(node: cst.Comparison) -> cst.Comparison | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        operator = comparison.operator
        comparator = comparison.comparator
        if isinstance(operator, cst.Equal) and is_none_name(comparator):
            return cst.Comparison(
                left=node.left,
                comparisons=[cst.ComparisonTarget(operator=cst.Is(), comparator=comparator)],
            )
        if isinstance(operator, cst.NotEqual) and is_none_name(comparator):
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
        return expr_replacement_hit(
            rule_id="none-compare",
            message="Prefer `is None` over `== None`",
            path=path,
            before_expr=node,
            after_expr=replacement,
        )
