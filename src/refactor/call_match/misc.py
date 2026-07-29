"""Miscellaneous libcst call pattern matchers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.call_match.basic import positional_call
from refactor.cst_util import is_true

if TYPE_CHECKING:
    from collections.abc import Sequence


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
