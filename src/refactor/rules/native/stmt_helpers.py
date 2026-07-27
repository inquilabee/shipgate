"""Shared statement-pattern helpers for native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.call_match import update_call_target
from refactor.cst_util import single_small_stmt

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


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


def negated_expr(expr: cst.BaseExpression) -> cst.BaseExpression:
    if isinstance(expr, cst.UnaryOperation) and isinstance(expr.operator, cst.Not):
        return expr.expression
    return cst.UnaryOperation(operator=cst.Not(), expression=expr)


def single_terminal_stmt(block: cst.IndentedBlock) -> cst.BaseSmallStatement | None:
    if len(block.body) != 1:
        return None
    line = block.body[0]
    if not isinstance(line, cst.SimpleStatementLine) or len(line.body) != 1:
        return None
    stmt = line.body[0]
    if isinstance(stmt, cst.Return | cst.Raise | cst.Break | cst.Continue):
        return stmt
    return None


def dict_update_to_union_stmt(
    node: cst.BaseSmallStatement,
) -> cst.BaseSmallStatement | None:
    if not isinstance(node, cst.Expr) or not isinstance(node.value, cst.Call):
        return None
    target = update_call_target(node.value)
    if target is None:
        return None
    return cst.AugAssign(
        target=target,
        operator=cst.BitOrAssign(),
        value=node.value.args[0].value,
    )


def method_call_stmt(
    stmt: cst.BaseStatement,
    method_name: str,
) -> tuple[cst.BaseExpression, list[cst.Arg]] | None:
    if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
        return None
    small_stmt = stmt.body[0]
    if not isinstance(small_stmt, cst.Expr) or not isinstance(small_stmt.value, cst.Call):
        return None
    call = small_stmt.value
    if not isinstance(call.func, cst.Attribute) or call.func.attr.value != method_name:
        return None
    return call.func.value, list(call.args)


def same_method_target(
    left: tuple[cst.BaseExpression, list[cst.Arg]] | None,
    right: tuple[cst.BaseExpression, list[cst.Arg]] | None,
) -> cst.BaseExpression | None:
    if left is None or right is None:
        return None
    target, _ = left
    right_target, _ = right
    return target if target.deep_equals(right_target) else None


def method_pair(
    body: Sequence[cst.BaseStatement],
    method_name: str,
) -> (
    tuple[
        cst.BaseStatement,
        cst.BaseStatement,
        cst.BaseExpression,
        list[cst.Arg],
        list[cst.Arg],
    ]
    | None
):
    for index, left_stmt in enumerate(body[:-1]):
        right_stmt = body[index + 1]
        left = method_call_stmt(left_stmt, method_name)
        right = method_call_stmt(right_stmt, method_name)
        target = same_method_target(left, right)
        if target is not None and left is not None and right is not None:
            return left_stmt, right_stmt, target, left[1], right[1]
    return None


def paired_method_collection_call(
    body: Sequence[cst.BaseStatement],
    *,
    source_method: str,
    replacement_method: str,
    collection_type: type[cst.List] | type[cst.Set],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    pair = method_pair(body, source_method)
    if pair is None:
        return None
    left_stmt, right_stmt, target, left_args, right_args = pair
    if len(left_args) != 1 or len(right_args) != 1:
        return None
    if left_args[0].keyword is not None or right_args[0].keyword is not None:
        return None
    return (
        [left_stmt, right_stmt],
        [
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Call(
                            func=cst.Attribute(value=target, attr=cst.Name(replacement_method)),
                            args=[
                                cst.Arg(
                                    value=collection_type(
                                        elements=[
                                            cst.Element(value=left_args[0].value),
                                            cst.Element(value=right_args[0].value),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


def list_appends_to_extend(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    return paired_method_collection_call(
        body,
        source_method="append",
        replacement_method="extend",
        collection_type=cst.List,
    )


def set_adds_to_update(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    return paired_method_collection_call(
        body,
        source_method="add",
        replacement_method="update",
        collection_type=cst.Set,
    )


def name_target_for_body_stmt(
    node: cst.CSTNode,
) -> tuple[cst.Name, cst.BaseExpression, cst.BaseSmallStatement] | None:
    if not isinstance(node, cst.For) or not isinstance(node.target, cst.Name):
        return None
    if not isinstance(node.body, cst.IndentedBlock):
        return None
    stmt = single_small_stmt(node.body)
    return None if stmt is None else (node.target, node.iter, stmt)


def two_item_tuple_target(node: cst.CSTNode) -> tuple[cst.Element, cst.Element] | None:
    if not isinstance(node, cst.For) or not isinstance(node.target, cst.Tuple):
        return None
    if len(node.target.elements) != 2:
        return None
    first, second = node.target.elements
    if not isinstance(first, cst.Element) or not isinstance(second, cst.Element):
        return None
    return first, second


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
    if not isinstance(stmt, cst.Assign) or len(stmt.targets) != 1:
        return None
    return stmt.targets[0].target, stmt.value


def duplicated_if_body(node: cst.CSTNode) -> Sequence[cst.BaseStatement] | None:
    blocks = if_else_blocks(node)
    if blocks is None:
        return None
    body, else_body = blocks
    return body.body if body.deep_equals(else_body) else None


def single_enumerate_arg(iter_expr: cst.BaseExpression) -> cst.BaseExpression | None:
    if not isinstance(iter_expr, cst.Call):
        return None
    if not isinstance(iter_expr.func, cst.Name) or iter_expr.func.value != "enumerate":
        return None
    if len(iter_expr.args) != 1 or iter_expr.args[0].keyword is not None:
        return None
    return iter_expr.args[0].value


def underscore_tuple_element(
    node: cst.CSTNode,
    *,
    position: int,
) -> cst.Element | None:
    if not isinstance(node, cst.For) or not isinstance(node.target, cst.Tuple):
        return None
    if len(node.target.elements) <= position:
        return None
    element = node.target.elements[position]
    if not isinstance(element, cst.Element):
        return None
    if not isinstance(element.value, cst.Name) or element.value.value != "_":
        return None
    return element


def dict_items_call(iter_expr: cst.BaseExpression) -> cst.Attribute | None:
    if not isinstance(iter_expr, cst.Call) or iter_expr.args:
        return None
    if not isinstance(iter_expr.func, cst.Attribute):
        return None
    return iter_expr.func if iter_expr.func.attr.value == "items" else None


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
        cast(
            "BodyStatement",
            node.with_changes(
                body=body.with_changes(body=left_body[:-1]),
                orelse=node.orelse.with_changes(
                    body=else_body.with_changes(body=right_body[:-1]),
                ),
            ),
        ),
        cast("BodyStatement", left_body[-1]),
    ]
