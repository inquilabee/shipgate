"""Native rule for ``simplify-fstring-formatting``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyFstringFormattingRule(PatternNativeRule):
    rule_id = "simplify-fstring-formatting"
    kind_value = "refactor"
    summary = "Simplify fstring formatting"
    needle = "simplify_fstring_formatting"
    replacement = "Review string pattern for simplify-fstring-formatting"
