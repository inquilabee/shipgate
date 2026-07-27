"""Native rule for ``use-or-for-fallback``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseOrForFallbackRule(PatternNativeRule):
    rule_id = "use-or-for-fallback"
    kind_value = "refactor"
    summary = "Use or for fallback"
    needle = "use_or_for_fallback"
    replacement = "Review loop pattern for use-or-for-fallback"
