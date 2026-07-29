"""If/else block helpers for native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import single_small_stmt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


def if_else_blocks(
    node: cst.CSTNode,
) -> tuple[cst.IndentedBlock, cst.IndentedBlock] | None:
    if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
        return None
    if not isinstance(node.body, cst.IndentedBlock):
        return None
    if not isinstance(node.orelse.body, cst.IndentedBlock):
        return None
    return node.body, node.orelse.body


def single_assign_block(
    block: cst.IndentedBlock,
) -> tuple[cst.BaseAssignTargetExpression, cst.BaseExpression] | None:
    stmt = single_small_stmt(block)
    return (
        None
        if not isinstance(stmt, cst.Assign) or len(stmt.targets) != 1
        else (stmt.targets[0].target, stmt.value)
    )


def duplicated_if_body(node: cst.CSTNode) -> Sequence[cst.BaseStatement] | None:
    blocks = if_else_blocks(node)
    if blocks is None:
        return None
    body, else_body = blocks
    return body.body if body.deep_equals(else_body) else None


def hoist_duplicate_trailing_stmt(node: cst.CSTNode) -> list[BodyStatement] | None:
    blocks = if_else_blocks(node)
    if blocks is None or not isinstance(node, cst.If):
        return None
    if not isinstance(node.orelse, cst.Else):
        return None
    body, else_body = blocks
    left_body = list(body.body)
    right_body = list(else_body.body)
    if not left_body or not right_body or not left_body[-1].deep_equals(right_body[-1]):
        return None
    return [
        node.with_changes(
            body=body.with_changes(body=left_body[:-1]),
            orelse=node.orelse.with_changes(
                body=else_body.with_changes(body=right_body[:-1]),
            ),
        ),
        left_body[-1],
    ]
