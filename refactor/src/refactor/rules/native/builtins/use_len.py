"""Replace ``len(x) == 0`` with ``not x`` for names and attributes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    detect_with_visitor,
    expr_replacement_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class UseLenRule:
    rule_id = "use-len"
    kind = RuleKind.REFACTOR
    summary = "Replace `len(x) == 0` with `not x`"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, UseLenRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Comparison(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.Comparison,
        ) -> bool:
            subject = UseLenRule.len_zero_subject(node)
            if subject is None:
                return True
            self.hits.append(UseLenRule.hit_for(node, subject, self.path))
            return True

    @staticmethod
    def len_zero_subject(node: cst.Comparison) -> cst.BaseExpression | None:
        if len(node.comparisons) != 1:
            return None
        comparison = node.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        if not UseLenRule.is_zero(comparison.comparator):
            return None
        if not isinstance(node.left, cst.Call):
            return None
        if not UseLenRule.is_len_call(node.left):
            return None
        if not node.left.args:
            return None
        subject = node.left.args[0].value
        if not isinstance(subject, (cst.Name, cst.Attribute)):
            return None
        return subject

    @staticmethod
    def is_len_call(node: cst.Call) -> bool:
        return isinstance(node.func, cst.Name) and node.func.value == "len"

    @staticmethod
    def is_zero(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer) and node.value == "0"

    @staticmethod
    def hit_for(
        node: cst.Comparison,
        subject: cst.BaseExpression,
        path: str,
    ) -> Hit:
        after_expr = cst.UnaryOperation(operator=cst.Not(), expression=subject)
        return expr_replacement_hit(
            rule_id="use-len",
            message="Prefer truthiness over `len(x) == 0`",
            path=path,
            before_expr=node,
            after_expr=after_expr,
        )
