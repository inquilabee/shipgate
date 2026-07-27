"""Native rule for ``use-isna``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseIsnaRule(PatternNativeRule):
    rule_id = "use-isna"
    kind_value = "refactor"
    summary = "Use isna"
    needle = "use_isna"
    replacement = "Review pandas pattern for use-isna"
