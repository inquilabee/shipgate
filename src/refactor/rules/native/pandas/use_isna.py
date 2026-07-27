"""Native rule for ``use-isna``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_none_name
from refactor.rules.native.expr_base import ComparisonRewriteRule


class UseIsnaRule(ComparisonRewriteRule):
    rule_id = "use-isna"
    summary = "Use isna"
    message = "Use pandas isna()/notna() for null comparisons"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        method_name = cls.isna_method_name(node.comparisons[0])
        if method_name is None:
            return None
        return cst.Call(func=cst.Attribute(value=node.left, attr=cst.Name(method_name)))

    @staticmethod
    def isna_method_name(target: cst.ComparisonTarget) -> str | None:
        if isinstance(target.operator, cst.Equal) and is_none_name(target.comparator):
            return "isna"
        if isinstance(target.operator, cst.NotEqual) and is_none_name(target.comparator):
            return "notna"
        return None
