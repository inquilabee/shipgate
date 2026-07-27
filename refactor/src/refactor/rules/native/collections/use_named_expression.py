"""Native rule for ``use-named-expression``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseNamedExpressionRule(PatternNativeRule):
    rule_id = "use-named-expression"
    kind_value = "refactor"
    summary = "Use named expression"
    needle = "use_named_expression"
    replacement = "Review Sourcery pattern for use-named-expression"
