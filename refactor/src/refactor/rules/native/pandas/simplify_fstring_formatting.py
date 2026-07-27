"""Native rule for ``simplify-fstring-formatting``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import FormattedStringRewriteRule


class SimplifyFstringFormattingRule(FormattedStringRewriteRule):
    rule_id = "simplify-fstring-formatting"
    summary = "Simplify fstring formatting"
    message = "Remove redundant !s conversion from f-string interpolation"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.FormattedString):
            return None
        parts = []
        changed = False
        for part in node.parts:
            if isinstance(part, cst.FormattedStringExpression) and part.conversion == "s":
                parts.append(part.with_changes(conversion=None))
                changed = True
            else:
                parts.append(part)
        return node.with_changes(parts=parts) if changed else None
