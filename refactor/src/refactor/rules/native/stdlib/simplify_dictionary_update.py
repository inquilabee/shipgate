"""Native rule for ``simplify-dictionary-update``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyDictionaryUpdateRule(PatternNativeRule):
    rule_id = "simplify-dictionary-update"
    kind_value = "refactor"
    summary = "Simplify dictionary update"
    needle = "simplify_dictionary_update"
    replacement = "Review dictionary pattern for simplify-dictionary-update"
