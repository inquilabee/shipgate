"""libcst call and comparison pattern matchers for refactor rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import is_true

if TYPE_CHECKING:
    from collections.abc import Sequence


def named_call(node: cst.CSTNode, name: str) -> cst.Call | None:
    if not isinstance(node, cst.Call):
        return None
    if not isinstance(node.func, cst.Name) or node.func.value != name:
        return None
    return node


def positional_call(node: cst.CSTNode, name: str, count: int) -> cst.Call | None:
    call = named_call(node, name)
    if call is None:
        return None
    if len(call.args) != count:
        return None
    if any(arg.keyword is not None for arg in call.args):
        return None
    return call


def single_positional_call(
    node: cst.CSTNode,
    name: str,
) -> tuple[cst.Call, cst.BaseExpression] | None:
    call = positional_call(node, name, 1)
    return None if call is None else (call, call.args[0].value)


def not_operation(node: cst.CSTNode) -> cst.UnaryOperation | None:
    return (
        None
        if not isinstance(node, cst.UnaryOperation) or not isinstance(node.operator, cst.Not)
        else node
    )


def attribute_method_call(node: cst.CSTNode, method: str) -> tuple[cst.Call, cst.Attribute] | None:
    if not isinstance(node, cst.Call):
        return None
    func = node.func
    if not isinstance(func, cst.Attribute) or func.attr.value != method:
        return None
    return node, func


def single_positional_method_call(
    node: cst.CSTNode,
    method: str,
) -> tuple[cst.Call, cst.Attribute, cst.BaseExpression] | None:
    pair = attribute_method_call(node, method)
    if pair is None:
        return None
    call, attr = pair
    if len(call.args) != 1 or call.args[0].keyword is not None:
        return None
    return call, attr, call.args[0].value


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


def split_inplace_keyword_args(
    args: Sequence[cst.Arg],
) -> tuple[list[cst.Arg], bool]:
    kept: list[cst.Arg] = []
    removed = False
    for arg in args:
        if arg.keyword is not None and arg.keyword.value == "inplace" and is_true(arg.value):
            removed = True
            continue
        kept.append(arg)
    return kept, removed


def literal_constructor_unwrap(
    node: cst.CSTNode,
    mapping: dict[str, type[cst.BaseExpression]],
) -> cst.BaseExpression | None:
    if not isinstance(node, cst.Call):
        return None
    if len(node.args) != 1 or node.args[0].keyword is not None:
        return None
    if not isinstance(node.func, cst.Name):
        return None
    literal_type = mapping.get(node.func.value)
    if literal_type is None:
        return None
    value = node.args[0].value
    return value if isinstance(value, literal_type) else None


def empty_attribute_call(
    node: cst.CSTNode,
    object_name: str,
    attribute: str,
) -> cst.Attribute | None:
    if not isinstance(node, cst.Call) or node.args:
        return None
    func = node.func
    if not isinstance(func, cst.Attribute):
        return None
    if not isinstance(func.value, cst.Name) or func.value.value != object_name:
        return None
    if func.attr.value != attribute:
        return None
    return func


def positional_call_any(
    node: cst.CSTNode,
    names: frozenset[str],
    count: int,
) -> cst.Call | None:
    for name in names:
        call = positional_call(node, name, count)
        if call is not None:
            return call
    return None


def decorator_names(decorators: Sequence[cst.Decorator]) -> set[str]:
    names: set[str] = set()
    for decorator in decorators:
        expression = decorator.decorator
        if isinstance(expression, cst.Name):
            names.add(expression.value)
        elif isinstance(expression, cst.Attribute):
            names.add(expression.attr.value)
    return names
