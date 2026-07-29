"""Method-call pattern helpers for native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

if TYPE_CHECKING:
    from collections.abc import Sequence


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
