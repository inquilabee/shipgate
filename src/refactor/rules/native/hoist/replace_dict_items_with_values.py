"""Native rule for ``replace-dict-items-with-values``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule
from refactor.rules.native.stmt_helpers import dict_items_call, underscore_tuple_element


class ReplaceDictItemsWithValuesRule(ForRewriteRule):
    rule_id = "replace-dict-items-with-values"
    summary = "Replace dict items with values"
    message = "Iterate over values when dict item keys are unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For):
            return None
        key = underscore_tuple_element(node, position=0)
        if key is None or not isinstance(node.target, cst.Tuple) or len(node.target.elements) != 2:
            return None
        value = node.target.elements[1]
        items_call = dict_items_call(node.iter)
        if items_call is None:
            return None
        return node.with_changes(
            target=value.value,
            iter=node.iter.with_changes(
                func=items_call.with_changes(attr=cst.Name("values")),
            ),
        )
