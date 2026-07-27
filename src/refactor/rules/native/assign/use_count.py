"""Native rule for ``use-count``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import equality_name_operand, single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class UseCountRule(CallRewriteRule):
    rule_id = "use-count"
    summary = "Use count"
    message = "Use collection.count(value) instead of summing equality matches"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "sum")
        if match is None:
            return None
        _, generator = match
        if not isinstance(generator, cst.GeneratorExp):
            return None
        counted = cls.counted_value(generator)
        if counted is None:
            return None
        return cst.Call(
            func=cst.Attribute(value=generator.for_in.iter, attr=cst.Name("count")),
            args=[cst.Arg(value=counted)],
        )

    @staticmethod
    def counted_value(generator: cst.GeneratorExp) -> cst.BaseExpression | None:
        if not isinstance(generator.elt, cst.Integer) or generator.elt.value != "1":
            return None
        if not isinstance(generator.for_in.target, cst.Name) or len(generator.for_in.ifs) != 1:
            return None
        return equality_name_operand(
            generator.for_in.ifs[0].test,
            generator.for_in.target.value,
        )

    @staticmethod
    def equality_target_for_name(
        condition: cst.BaseExpression,
        target_name: str,
    ) -> cst.BaseExpression | None:
        return equality_name_operand(condition, target_name)
