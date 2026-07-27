"""Native rule for ``pandas-avoid-inplace``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_true
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
        args = []
        removed = False
        for arg in node.args:
            if arg.keyword is not None and arg.keyword.value == "inplace" and is_true(arg.value):
                removed = True
                continue
            args.append(arg)
        if not removed:
            return None
        if args:
            args[-1] = args[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return node.with_changes(args=args)
