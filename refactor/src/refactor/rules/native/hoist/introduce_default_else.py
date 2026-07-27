"""Native rule for ``introduce-default-else``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class IntroduceDefaultElseRule(PatternNativeRule):
    rule_id = "introduce-default-else"
    kind_value = "refactor"
    summary = "Introduce default else"
    needle = "introduce_default_else"
    replacement = "Review conditional pattern for introduce-default-else"
