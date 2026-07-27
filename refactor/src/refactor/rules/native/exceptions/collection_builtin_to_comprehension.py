"""Native rule for ``collection-builtin-to-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class CollectionBuiltinToComprehensionRule(PatternNativeRule):
    rule_id = "collection-builtin-to-comprehension"
    kind_value = "refactor"
    summary = "Collection builtin to comprehension"
    needle = "collection_builtin_to_comprehension"
    replacement = "Review collection pattern for collection-builtin-to-comprehension"
