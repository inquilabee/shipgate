"""Statement-level libcst pattern matchers for refactor rules."""

from __future__ import annotations

import libcst as cst


def single_assign_from_stmt(stmt: cst.BaseStatement) -> cst.Assign | None:
    if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
        return None
    assign = stmt.body[0]
    if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
        return None
    return assign


def for_without_else_single_body(
    node: cst.CSTNode,
) -> tuple[cst.For, cst.BaseStatement] | None:
    if not isinstance(node, cst.For) or node.orelse is not None:
        return None
    if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
        return None
    return node, node.body.body[0]


def if_without_else_single_body(
    node: cst.CSTNode,
) -> tuple[cst.If, cst.BaseStatement] | None:
    if not isinstance(node, cst.If) or node.orelse is not None:
        return None
    if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
        return None
    return node, node.body.body[0]
