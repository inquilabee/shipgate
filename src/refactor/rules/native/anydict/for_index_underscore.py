"""Native rule for ``for-index-underscore``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, two_item_tuple_target
from refactor.rules.native.stmt_helpers import single_enumerate_arg


class ForIndexUnderscoreRule(ForRewriteRule):
    rule_id = "for-index-underscore"
    summary = "For index underscore"
    message = "Use range when enumerate values are unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        target = two_item_tuple_target(node)
        if target is None or not isinstance(node, cst.For):
            return None
        index, value = target
        if not isinstance(value.value, cst.Name) or value.value.value != "_":
            return None
        sequence = single_enumerate_arg(node.iter)
        if sequence is None:
            return None
        return node.with_changes(
            target=index.value,
            iter=cst.Call(
                func=cst.Name("range"),
                args=[
                    cst.Arg(
                        value=cst.Call(
                            func=cst.Name("len"),
                            args=[cst.Arg(value=sequence)],
                        ),
                    ),
                ],
            ),
        )
