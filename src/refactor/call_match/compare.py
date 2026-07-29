"""Comparison and method-call libcst pattern matchers."""

from __future__ import annotations

import libcst as cst

from refactor.call_match.basic import attribute_method_call


def update_call_target(call: cst.Call) -> cst.BaseAssignTargetExpression | None:
    pair = attribute_method_call(call, "update")
    if pair is None:
        return None
    _, attr = pair
    if len(call.args) != 1 or call.args[0].keyword is not None:
        return None
    value = attr.value
    if not isinstance(value, cst.Name | cst.Attribute | cst.Subscript):
        return None
    return value


def equality_name_operand(
    condition: cst.BaseExpression,
    name: str,
) -> cst.BaseExpression | None:
    if not isinstance(condition, cst.Comparison) or len(condition.comparisons) != 1:
        return None
    target = condition.comparisons[0]
    if not isinstance(target.operator, cst.Equal):
        return None
    return equality_name_side(condition.left, target.comparator, name)


def equality_name_side(
    left: cst.BaseExpression,
    right: cst.BaseExpression,
    name: str,
) -> cst.BaseExpression | None:
    return (
        right
        if isinstance(left, cst.Name) and left.value == name
        else left
        if isinstance(right, cst.Name) and right.value == name
        else None
    )


def adjacent_and_comparisons(
    node: cst.CSTNode,
) -> tuple[cst.Comparison, cst.Comparison] | None:
    if not isinstance(node, cst.BooleanOperation) or not isinstance(node.operator, cst.And):
        return None
    left = node.left
    right = node.right
    if not isinstance(left, cst.Comparison) or not isinstance(right, cst.Comparison):
        return None
    if len(left.comparisons) != 1 or len(right.comparisons) != 1:
        return None
    return left, right


def inverted_equal_operator(operator: cst.BaseCompOp) -> cst.BaseCompOp | None:
    return (
        cst.NotEqual()
        if isinstance(operator, cst.Equal)
        else cst.Equal()
        if isinstance(operator, cst.NotEqual)
        else None
    )


def two_positional_method_call(
    node: cst.CSTNode,
    method: str,
) -> tuple[cst.Call, cst.Attribute, cst.BaseExpression, cst.BaseExpression] | None:
    pair = attribute_method_call(node, method)
    if pair is None:
        return None
    call, attr = pair
    if len(call.args) != 2 or any(arg.keyword is not None for arg in call.args):
        return None
    return call, attr, call.args[0].value, call.args[1].value
