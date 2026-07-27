"""Replace interpolation-free f-strings like ``f"hello"`` with plain strings."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import FormattedStringRewriteRule


class RemoveRedundantFstringRule(FormattedStringRewriteRule):
    rule_id = "remove-redundant-fstring"
    summary = "Replace f-strings without interpolations with plain strings"
    message = "Remove redundant f-string prefix"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.FormattedString):
            return None
        if not node.parts:
            return None
        text = ""
        for part in node.parts:
            if not isinstance(part, cst.FormattedStringText):
                return None
            text += part.value
        quote = '"' if node.start.endswith('"') else "'"
        return cst.SimpleString(f"{quote}{text}{quote}")
