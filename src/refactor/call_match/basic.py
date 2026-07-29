"""Basic libcst call pattern matchers."""

from __future__ import annotations

import libcst as cst


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
