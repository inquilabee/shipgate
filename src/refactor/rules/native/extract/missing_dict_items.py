"""Native rule for ``missing-dict-items``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, two_item_tuple_target


class MissingDictItemsRule(ForRewriteRule):
    rule_id = "missing-dict-items"
    summary = "Missing dict items"
    message = "Iterate over dictionary items when unpacking key and value"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if two_item_tuple_target(node) is None or not isinstance(node, cst.For):
            return None
        if isinstance(node.iter, cst.Call):
            return None
        return node.with_changes(
            iter=cst.Call(
                func=cst.Attribute(value=node.iter, attr=cst.Name("items")),
                args=[],
            ),
        )
