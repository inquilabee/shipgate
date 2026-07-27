"""Native rule for ``replace-dict-items-with-values``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule


class ReplaceDictItemsWithValuesRule(ForRewriteRule):
    rule_id = "replace-dict-items-with-values"
    summary = "Replace dict items with values"
    message = "Iterate over values when dict item keys are unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For):
            return None
        if not isinstance(node.target, cst.Tuple) or len(node.target.elements) != 2:
            return None
        key, value = node.target.elements
        if not isinstance(key.value, cst.Name) or key.value.value != "_":
            return None
        if not isinstance(node.iter, cst.Call) or node.iter.args:
            return None
        if not isinstance(node.iter.func, cst.Attribute):
            return None
        if node.iter.func.attr.value != "items":
            return None
        return node.with_changes(
            target=value.value,
            iter=node.iter.with_changes(
                func=node.iter.func.with_changes(attr=cst.Name("values")),
            ),
        )
