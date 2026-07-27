"""Native rule for ``remove-unused-enumerate``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule


class RemoveUnusedEnumerateRule(ForRewriteRule):
    rule_id = "remove-unused-enumerate"
    summary = "Remove unused enumerate"
    message = "Remove enumerate when the index is unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For):
            return None
        if not isinstance(node.target, cst.Tuple) or len(node.target.elements) != 2:
            return None
        index, value = node.target.elements
        if not isinstance(index.value, cst.Name) or index.value.value != "_":
            return None
        if not isinstance(node.iter, cst.Call):
            return None
        if not isinstance(node.iter.func, cst.Name) or node.iter.func.value != "enumerate":
            return None
        if len(node.iter.args) != 1 or node.iter.args[0].keyword is not None:
            return None
        return node.with_changes(target=value.value, iter=node.iter.args[0].value)
