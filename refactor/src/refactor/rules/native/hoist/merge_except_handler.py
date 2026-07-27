"""Native rule for ``merge-except-handler``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import TryRewriteRule


class MergeExceptHandlerRule(TryRewriteRule):
    rule_id = "merge-except-handler"
    summary = "Merge except handler"
    message = "Merge except handlers with identical bodies"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.Try):
            return None
        for index, left in enumerate(node.handlers[:-1]):
            right = node.handlers[index + 1]
            if left.name is not None or right.name is not None:
                continue
            if left.type is None or right.type is None:
                continue
            if not left.body.deep_equals(right.body):
                continue
            merged = left.with_changes(
                type=cst.Tuple(
                    elements=[
                        cst.Element(value=left.type),
                        cst.Element(value=right.type),
                    ],
                    lpar=[],
                    rpar=[],
                ),
            )
            return node.with_changes(
                handlers=[*node.handlers[:index], merged, *node.handlers[index + 2 :]],
            )
        return None
