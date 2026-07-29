"""Native rule for ``simplify-constant-sum`` (external refactor parity)."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class SimplifyConstantSumRule(CallRewriteRule):
    rule_id = "simplify-constant-sum"
    summary = "Simplify constant sum() call"
    message = "Replace sum(1 for ... if cond) with sum(cond for ...)"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        matched = single_positional_call(node, "sum")
        if matched is None:
            return None
        call, argument = matched
        if not isinstance(argument, cst.GeneratorExp):
            return None
        rewritten = cls.bool_generator(argument)
        if rewritten is None:
            return None
        return call.with_changes(args=[cst.Arg(value=rewritten)])

    @classmethod
    def bool_generator(cls, generator: cst.GeneratorExp) -> cst.GeneratorExp | None:
        if not cls.is_constant_one(generator.elt):
            return None
        for_in = generator.for_in
        if for_in.inner_for_in is not None or len(for_in.ifs) != 1:
            return None
        condition = for_in.ifs[0].test
        return generator.with_changes(
            elt=condition,
            for_in=for_in.with_changes(ifs=()),
        )

    @staticmethod
    def is_constant_one(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer) and node.value.replace("_", "") == "1"
