"""Replace empty ``tuple()`` with ``()``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    apply_with_transformer,
    detect_with_visitor,
    expr_replacement_hit,
    is_empty_call,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class TupleLiteralRule:
    rule_id = "tuple-literal"
    kind = RuleKind.REFACTOR
    summary = "Replace empty `tuple()` with `()`"
    apply_mode = ApplyMode.AUTO

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, TupleLiteralRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, TupleLiteralRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Call(
            self,
            original_node: cst.Call,
            updated_node: cst.Call,
        ) -> cst.BaseExpression:
            _ = self, original_node
            return cst.Tuple(elements=[]) if is_empty_call(updated_node, "tuple") else updated_node

    class Finder(HitCollector):
        def visit_Call(self, node: cst.Call) -> bool:
            if not is_empty_call(node, "tuple"):
                return True
            self.hits.append(TupleLiteralRule.hit_for(node, self.path))
            return True

    @staticmethod
    def hit_for(node: cst.Call, path: str) -> Hit:
        return expr_replacement_hit(
            rule_id="tuple-literal",
            message="Prefer `()` over empty tuple()",
            path=path,
            before_expr=node,
            after_expr=cst.Tuple(elements=[]),
        )
