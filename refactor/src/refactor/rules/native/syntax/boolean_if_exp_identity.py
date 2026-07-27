"""Simplify boolean ``if`` expressions like ``True if cond else False``."""

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


class BooleanIfExpIdentityRule:
    rule_id = "boolean-if-exp-identity"
    kind = RuleKind.REFACTOR
    summary = "Simplify `True if cond else False` to `cond`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, BooleanIfExpIdentityRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_IfExp(self, node: cst.IfExp) -> bool:  # ruff:ignore[invalid-function-name]
            replacement = BooleanIfExpIdentityRule.match_identity(node)
            if replacement is None:
                return True
            self.hits.append(BooleanIfExpIdentityRule.hit_for(node, replacement, self.path))
            return True

    @staticmethod
    def match_identity(node: cst.IfExp) -> cst.BaseExpression | None:
        if is_true(node.body) and is_false(node.orelse):
            return node.test
        if is_false(node.body) and is_true(node.orelse):
            return cst.UnaryOperation(operator=cst.Not(), expression=node.test)
        return None

    @staticmethod
    def hit_for(
        node: cst.IfExp,
        replacement: cst.BaseExpression,
        path: str,
    ) -> Hit:
        return expr_replacement_hit(
            rule_id="boolean-if-exp-identity",
            message="Simplify boolean if-expression",
            path=path,
            before_expr=node,
            after_expr=replacement,
        )
