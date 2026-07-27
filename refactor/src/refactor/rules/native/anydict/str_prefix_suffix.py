"""Native rule for ``str-prefix-suffix``."""

from __future__ import annotations

import ast

import libcst as cst

from refactor.cst_util import parse_integer_literal
from refactor.rules.native.expr_base import ComparisonRewriteRule


class StrPrefixSuffixRule(ComparisonRewriteRule):
    rule_id = "str-prefix-suffix"
    summary = "Str prefix suffix"
    message = "Use startswith() or endswith() for prefix and suffix checks"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        target = node.comparisons[0]
        if not isinstance(target.operator, cst.Equal):
            return None
        return cls.build_replacement(node.left, target.comparator) or cls.build_replacement(
            target.comparator,
            node.left,
        )

    @classmethod
    def build_replacement(
        cls,
        sliced: cst.BaseExpression,
        expected: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        if not isinstance(expected, cst.SimpleString):
            return None
        expected_value = cls.string_value(expected)
        if expected_value is None:
            return None
        match = cls.slice_match(sliced, len(expected_value))
        if match is None:
            return None
        receiver, method_name = match
        return cst.Call(
            func=cst.Attribute(value=receiver, attr=cst.Name(method_name)),
            args=[cst.Arg(value=expected)],
        )

    @staticmethod
    def string_value(node: cst.SimpleString) -> str | None:
        value = ast.literal_eval(node.value)
        return value if isinstance(value, str) else None

    @classmethod
    def slice_match(
        cls,
        node: cst.BaseExpression,
        expected_len: int,
    ) -> tuple[cst.BaseExpression, str] | None:
        if not isinstance(node, cst.Subscript) or len(node.slice) != 1:
            return None
        subscript = node.slice[0].slice
        if not isinstance(subscript, cst.Slice):
            return None
        if subscript.lower is None and cls.integer_value(subscript.upper) == expected_len:
            return node.value, "startswith"
        if subscript.upper is None and cls.integer_value(subscript.lower) == -expected_len:
            return node.value, "endswith"
        return None

    @staticmethod
    def integer_value(node: cst.BaseExpression | None) -> int | None:
        if isinstance(node, cst.Integer):
            return parse_integer_literal(node.value)
        if (
            isinstance(node, cst.UnaryOperation)
            and isinstance(node.operator, cst.Minus)
            and isinstance(node.expression, cst.Integer)
        ):
            value = parse_integer_literal(node.expression.value)
            return None if value is None else -value
        return None
