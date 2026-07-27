"""Native rule for ``simplify-empty-collection-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyEmptyCollectionComparisonRule(PatternNativeRule):
    rule_id = "simplify-empty-collection-comparison"
    kind_value = "refactor"
    summary = "Simplify empty collection comparison"
    needle = "simplify_empty_collection_comparison"
    replacement = "Review collection pattern for simplify-empty-collection-comparison"
