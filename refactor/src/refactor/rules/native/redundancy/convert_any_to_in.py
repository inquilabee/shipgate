"""Native rule for ``convert-any-to-in``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class ConvertAnyToInRule(CallRewriteRule):
    rule_id = "convert-any-to-in"
    summary = "Convert any to in"
    message = "Use membership testing instead of any() with equality"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "any":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        generator = node.args[0].value
        if not isinstance(generator, cst.GeneratorExp):
            return None
        match = cls.equality_match(generator)
        if match is None:
            return None
        needle, iterable = match
        return cst.Comparison(
            left=needle,
            comparisons=[cst.ComparisonTarget(operator=cst.In(), comparator=iterable)],
        )

    @staticmethod
    def equality_match(
        generator: cst.GeneratorExp,
    ) -> tuple[cst.BaseExpression, cst.BaseExpression] | None:
        if not isinstance(generator.for_in.target, cst.Name):
            return None
        if not isinstance(generator.elt, cst.Comparison) or len(generator.elt.comparisons) != 1:
            return None
        target_name = generator.for_in.target.value
        comparison = generator.elt.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        if isinstance(generator.elt.left, cst.Name) and generator.elt.left.value == target_name:
            return comparison.comparator, generator.for_in.iter
        if (
            isinstance(comparison.comparator, cst.Name)
            and comparison.comparator.value == target_name
        ):
            return generator.elt.left, generator.for_in.iter
        return None
