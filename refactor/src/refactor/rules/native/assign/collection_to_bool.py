"""Native rule for ``collection-to-bool``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class CollectionToBoolRule(PatternNativeRule):
    rule_id = "collection-to-bool"
    kind_value = "refactor"
    summary = "Collection to bool"
    needle = "collection_to_bool"
    replacement = "Review collection pattern for collection-to-bool"
