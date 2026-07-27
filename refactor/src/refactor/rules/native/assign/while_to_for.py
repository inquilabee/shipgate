"""Native rule for ``while-to-for``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class WhileToForRule(PatternNativeRule):
    rule_id = "while-to-for"
    kind_value = "refactor"
    summary = "While to for"
    needle = "while_to_for"
    replacement = "Review loop pattern for while-to-for"
