"""Native rule for ``unwrap-iterable-construction``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import literal_constructor_unwrap
from refactor.rules.native.expr_base import CallRewriteRule

LITERAL_BY_CONSTRUCTOR: dict[str, type[cst.BaseExpression]] = {
    "list": cst.List,
    "tuple": cst.Tuple,
    "set": cst.Set,
}


class UnwrapIterableConstructionRule(CallRewriteRule):
    rule_id = "unwrap-iterable-construction"
    summary = "Unwrap iterable construction"
    message = "Remove redundant collection construction around the same literal type"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return literal_constructor_unwrap(node, LITERAL_BY_CONSTRUCTOR)
