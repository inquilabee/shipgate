"""Native rule for ``use-dictionary-union``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseDictionaryUnionRule(PatternNativeRule):
    rule_id = "use-dictionary-union"
    kind_value = "refactor"
    summary = "Use dictionary union"
    needle = "use_dictionary_union"
    replacement = "Review dictionary pattern for use-dictionary-union"
