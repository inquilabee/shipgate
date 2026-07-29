"""If-statement merge helpers for native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

if TYPE_CHECKING:
    from collections.abc import Sequence


def merge_adjacent_ifs_with_same_test(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    for index, left in enumerate(body[:-1]):
        right = body[index + 1]
        if not isinstance(left, cst.If) or not isinstance(right, cst.If):
            continue
        if left.orelse is not None or right.orelse is not None:
            continue
        if not isinstance(left.body, cst.IndentedBlock) or not isinstance(
            right.body,
            cst.IndentedBlock,
        ):
            continue
        if not left.test.deep_equals(right.test):
            continue
        return (
            [left, right],
            [
                left.with_changes(
                    body=left.body.with_changes(body=[*left.body.body, *right.body.body]),
                ),
            ],
        )
    return None


def merge_nested_if(node: cst.CSTNode) -> cst.BaseStatement | None:
    if not isinstance(node, cst.If) or node.orelse is not None:
        return None
    if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
        return None
    inner = node.body.body[0]
    if not isinstance(inner, cst.If):
        return None
    return node.with_changes(
        test=cst.BooleanOperation(left=node.test, operator=cst.And(), right=inner.test),
        body=inner.body,
        orelse=inner.orelse,
    )
