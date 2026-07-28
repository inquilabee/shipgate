"""Replace empty ``dict()`` with ``{}``."""

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
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class DictLiteralRule:
    rule_id = "dict-literal"
    kind = RuleKind.REFACTOR
    summary = "Replace empty `dict()` with `{}`"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, DictLiteralRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return apply_with_transformer(source, DictLiteralRule.Transformer())

    class Transformer(cst.CSTTransformer):
        def leave_Call(  # ruff:ignore[invalid-function-name]
            self,
            original_node: cst.Call,
            updated_node: cst.Call,
        ) -> cst.BaseExpression:
            _ = self, original_node
            return cst.Dict(elements=[]) if is_empty_call(updated_node, "dict") else updated_node

    class Finder(HitCollector):
        def visit_Call(self, node: cst.Call) -> bool:  # ruff:ignore[invalid-function-name]
            if not is_empty_call(node, "dict"):
                return True
            self.record_hit(DictLiteralRule.hit_for(node, self.path), node)
            return True

    @staticmethod
    def hit_for(node: cst.Call, path: str) -> Hit:
        return expr_replacement_hit(
            rule_id="dict-literal",
            message="Prefer `{}` over empty dict()",
            path=path,
            before_expr=node,
            after_expr=cst.Dict(elements=[]),
        )
