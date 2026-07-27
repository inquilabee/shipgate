"""Native rule for ``use-string-remove-affix``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseStringRemoveAffixRule(PatternNativeRule):
    rule_id = "use-string-remove-affix"
    kind_value = "refactor"
    summary = "Use string remove affix"
    needle = "use_string_remove_affix"
    replacement = "Review string pattern for use-string-remove-affix"
