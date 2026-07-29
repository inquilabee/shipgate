"""Replace min/max ternaries with ``min()`` / ``max()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    apply_with_transformer,
    detect_with_visitor,
    expr_replacement_hit,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class MinMaxIdentityRule:
    rule_id = "min-max-identity"
    kind = RuleKind.REFACTOR
    summary = "Replace `x if x < y else y` with `min(x, y)`"
    apply_mode = ApplyMode.AUTO

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, MinMaxIdentityRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, MinMaxIdentityRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_IfExp(
            self,
            original_node: cst.IfExp,
            updated_node: cst.IfExp,
        ) -> cst.BaseExpression:
            _ = self, original_node
            match = MinMaxIdentityRule.match_min_max(updated_node)
            if match is None:
                return updated_node
            func_name, left, right = match
            return cst.Call(
                func=cst.Name(func_name),
                args=[cst.Arg(value=left), cst.Arg(value=right)],
            )

    class Finder(HitCollector):
        def visit_IfExp(self, node: cst.IfExp) -> bool:
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
        return (
            ("min", node.body, node.orelse)
            if isinstance(operator, cst.LessThan)
            else (
                ("max", node.body, node.orelse) if isinstance(operator, cst.GreaterThan) else None
            )
        )

    @staticmethod
    def hit_for(
        node: cst.IfExp,
        func_name: str,
        left: cst.BaseExpression,
        right: cst.BaseExpression,
        path: str,
    ) -> Hit:
        after_expr = cst.Call(
            func=cst.Name(func_name),
            args=[cst.Arg(value=left), cst.Arg(value=right)],
        )
        return expr_replacement_hit(
            rule_id="min-max-identity",
            message=f"Prefer `{func_name}()` over conditional",
            path=path,
            before_expr=node,
            after_expr=after_expr,
        )
