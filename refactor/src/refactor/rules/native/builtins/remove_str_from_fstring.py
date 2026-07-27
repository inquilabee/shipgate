"""Replace ``f"{str(x)}"`` with ``f"{x}"``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import unwrap_str_call
from refactor.rules.native.expr_base import FormattedStringRewriteRule


class RemoveStrFromFstringRule(FormattedStringRewriteRule):
    rule_id = "remove-str-from-fstring"
    summary = "Remove redundant str() inside f-string interpolation"
    message = "Remove redundant str() in f-string"

    @classmethod
    def match(cls, node: cst.FormattedString) -> cst.BaseExpression | None:
        if len(node.parts) != 1:
            return None
        part = node.parts[0]
        if not isinstance(part, cst.FormattedStringExpression):
            return None
        inner = unwrap_str_call(part.expression)
        if inner is None:
            return None
        return node.with_changes(parts=[part.with_changes(expression=inner)])
