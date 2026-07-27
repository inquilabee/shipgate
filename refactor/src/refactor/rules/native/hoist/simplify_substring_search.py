"""Native rule for ``simplify-substring-search``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifySubstringSearchRule(PatternNativeRule):
    rule_id = "simplify-substring-search"
    kind_value = "refactor"
    summary = "Simplify substring search"
    needle = "simplify_substring_search"
    replacement = "Review string pattern for simplify-substring-search"
