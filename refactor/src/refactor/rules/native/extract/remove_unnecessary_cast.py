"""Native rule for ``remove-unnecessary-cast``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveUnnecessaryCastRule(PatternNativeRule):
    rule_id = "remove-unnecessary-cast"
    kind_value = "refactor"
    summary = "Remove unnecessary cast"
    needle = "remove_unnecessary_cast"
    replacement = "Review Sourcery pattern for remove-unnecessary-cast"
