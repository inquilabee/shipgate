"""For-loop pattern helpers for native rewrite rules."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt


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
