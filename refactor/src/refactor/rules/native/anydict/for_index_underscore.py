"""Native rule for ``for-index-underscore``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule


class ForIndexUnderscoreRule(ForRewriteRule):
    rule_id = "for-index-underscore"
    summary = "For index underscore"
    message = "Use range when enumerate values are unused"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For):
            return None
        if not isinstance(node.target, cst.Tuple) or len(node.target.elements) != 2:
            return None
        index, value = node.target.elements
        if not isinstance(value.value, cst.Name) or value.value.value != "_":
            return None
        if not isinstance(node.iter, cst.Call):
            return None
        if not isinstance(node.iter.func, cst.Name) or node.iter.func.value != "enumerate":
            return None
        if len(node.iter.args) != 1 or node.iter.args[0].keyword is not None:
            return None
        return node.with_changes(
            target=index.value,
            iter=cst.Call(
                func=cst.Name("range"),
                args=[
                    cst.Arg(
                        value=cst.Call(
                            func=cst.Name("len"),
                            args=[cst.Arg(value=node.iter.args[0].value)],
                        ),
                    ),
                ],
            ),
        )
