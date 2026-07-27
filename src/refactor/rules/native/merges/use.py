"""Native rule for ``use``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseRule(PatternNativeRule):
    rule_id = "use"
    kind_value = "refactor"
    summary = "Use"
    needle = ""
    replacement = "use is registered as comment-only"
