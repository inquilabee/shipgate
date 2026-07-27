"""Native rule for ``simplify-generator``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyGeneratorRule(PatternNativeRule):
    rule_id = "simplify-generator"
    kind_value = "refactor"
    summary = "Simplify generator"
    needle = "simplify_generator"
    replacement = "Review conditional pattern for simplify-generator"
