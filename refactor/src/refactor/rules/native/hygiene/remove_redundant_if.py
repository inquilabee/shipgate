"""Native rule for ``remove-redundant-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantIfRule(PatternNativeRule):
    rule_id = "remove-redundant-if"
    kind_value = "refactor"
    summary = "Remove redundant if"
    needle = "remove_redundant_if"
    replacement = "Review conditional pattern for remove-redundant-if"
