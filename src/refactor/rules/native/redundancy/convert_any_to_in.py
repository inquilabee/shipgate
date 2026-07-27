"""Native rule for ``convert-any-to-in``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import equality_name_side, single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class ConvertAnyToInRule(CallRewriteRule):
    rule_id = "convert-any-to-in"
    summary = "Convert any to in"
    message = "Use membership testing instead of any() with equality"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "any")
        if match is None:
            return None
        _, generator = match
        if not isinstance(generator, cst.GeneratorExp):
            return None
        equality = cls.equality_match(generator)
        if equality is None:
            return None
        needle, iterable = equality
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
        comparison = generator.elt.comparisons[0]
        if not isinstance(comparison.operator, cst.Equal):
            return None
        target_name = generator.for_in.target.value
        needle = equality_name_side(
            generator.elt.left,
            comparison.comparator,
            target_name,
        )
        if needle is None:
            return None
        return needle, generator.for_in.iter
