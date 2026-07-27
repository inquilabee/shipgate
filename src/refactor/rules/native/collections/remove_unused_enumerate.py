"""Native rule for ``remove-unused-enumerate``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, two_item_tuple_target
from refactor.rules.native.stmt_helpers import single_enumerate_arg


class RemoveUnusedEnumerateRule(ForRewriteRule):
    rule_id = "remove-unused-enumerate"
    summary = "Remove unused enumerate"
    message = "Remove enumerate when the index is unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        target = two_item_tuple_target(node)
        if target is None or not isinstance(node, cst.For):
            return None
        index, value = target
        if not isinstance(index.value, cst.Name) or index.value.value != "_":
            return None
        sequence = single_enumerate_arg(node.iter)
        if sequence is None:
            return None
        return node.with_changes(target=value.value, iter=sequence)
