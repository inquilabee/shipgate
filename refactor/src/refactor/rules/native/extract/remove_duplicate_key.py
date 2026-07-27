"""Native rule for ``remove-duplicate-key``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import code_for_expr
from refactor.rules.native.expr_base import DictRewriteRule


class RemoveDuplicateKeyRule(DictRewriteRule):
    rule_id = "remove-duplicate-key"
    summary = "Remove duplicate key"
    message = "Remove duplicate dictionary keys that are overwritten later"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Dict):
            return None
        seen: set[str] = set()
        keep_reversed = []
        removed_duplicate = False
        for element in reversed(node.elements):
            if not isinstance(element, cst.DictElement):
                keep_reversed.append(element)
                continue
            key = code_for_expr(element.key)
            if key in seen:
                removed_duplicate = True
                continue
            seen.add(key)
            keep_reversed.append(element)
        if not removed_duplicate:
            return None
        return node.with_changes(elements=list(reversed(keep_reversed)))
