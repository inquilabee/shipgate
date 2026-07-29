"""Shared statement-pattern helpers for native rewrite rules."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import update_call_target
from refactor.rules.native.stmt_if_blocks import (
    duplicated_if_body,
    hoist_duplicate_trailing_stmt,
    if_else_blocks,
    single_assign_block,
)
from refactor.rules.native.stmt_if_merge import (
    merge_adjacent_ifs_with_same_test,
    merge_nested_if,
)
from refactor.rules.native.stmt_loop_helpers import (
    dict_items_call,
    name_target_for_body_stmt,
    single_enumerate_arg,
    two_item_tuple_target,
    underscore_tuple_element,
)
from refactor.rules.native.stmt_method_helpers import (
    list_appends_to_extend,
    method_call_stmt,
    method_pair,
    paired_method_collection_call,
    same_method_target,
    set_adds_to_update,
)

__all__ = [
    "dict_items_call",
    "dict_update_to_union_stmt",
    "duplicated_if_body",
    "hoist_duplicate_trailing_stmt",
    "if_else_blocks",
    "list_appends_to_extend",
    "merge_adjacent_ifs_with_same_test",
    "merge_nested_if",
    "method_call_stmt",
    "method_pair",
    "name_target_for_body_stmt",
    "negated_expr",
    "paired_method_collection_call",
    "same_method_target",
    "set_adds_to_update",
    "single_assign_block",
    "single_enumerate_arg",
    "single_terminal_stmt",
    "two_item_tuple_target",
    "underscore_tuple_element",
]


def negated_expr(expr: cst.BaseExpression) -> cst.BaseExpression:
    return (
        expr.expression
        if isinstance(expr, cst.UnaryOperation) and isinstance(expr.operator, cst.Not)
        else cst.UnaryOperation(operator=cst.Not(), expression=expr)
    )


def single_terminal_stmt(block: cst.IndentedBlock) -> cst.BaseSmallStatement | None:
    if len(block.body) != 1:
        return None
    line = block.body[0]
    if not isinstance(line, cst.SimpleStatementLine) or len(line.body) != 1:
        return None
    stmt = line.body[0]
    return stmt if isinstance(stmt, cst.Return | cst.Raise | cst.Break | cst.Continue) else None


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
