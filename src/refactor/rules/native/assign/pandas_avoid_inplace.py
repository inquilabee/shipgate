"""Native rule for ``pandas-avoid-inplace``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import split_inplace_keyword_args
from refactor.protocol import RuleKind
from refactor.rules.native.expr_base import CallRewriteRule


class PandasAvoidInplaceRule(CallRewriteRule):
    rule_id = "pandas-avoid-inplace"
    kind = RuleKind.SUGGESTION
    summary = "Pandas avoid inplace"
    message = "Avoid pandas inplace=True operations"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        args, removed = split_inplace_keyword_args(node.args)
        if not removed:
            return None
        if args:
            args[-1] = args[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return node.with_changes(args=args)
