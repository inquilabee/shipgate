"""Native rule for ``use-count``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseCountRule(CallRewriteRule):
    rule_id = "use-count"
    summary = "Use count"
    message = "Use collection.count(value) instead of summing equality matches"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "sum":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        generator = node.args[0].value
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
        condition = generator.for_in.ifs[0].test
        if not isinstance(condition, cst.Comparison) or len(condition.comparisons) != 1:
            return None
        target = condition.comparisons[0]
        if not isinstance(target.operator, cst.Equal):
            return None
        target_name = generator.for_in.target.value
        if isinstance(condition.left, cst.Name) and condition.left.value == target_name:
            return target.comparator
        if isinstance(target.comparator, cst.Name) and target.comparator.value == target_name:
            return condition.left
        return None
