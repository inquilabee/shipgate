"""Native rule for ``remove-duplicate-set-key``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import code_for_expr
from refactor.rules.native.expr_base import SetRewriteRule


class RemoveDuplicateSetKeyRule(SetRewriteRule):
    rule_id = "remove-duplicate-set-key"
    summary = "Remove duplicate set key"
    message = "Remove duplicate set literal entries"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Set):
            return None
        seen: set[str] = set()
        elements = []
        removed_duplicate = False
        for element in node.elements:
            value = code_for_expr(element.value)
            if value in seen:
                removed_duplicate = True
            else:
                seen.add(value)
                elements.append(element)
        if not removed_duplicate:
            return None
        elements[-1] = elements[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return node.with_changes(elements=elements)
