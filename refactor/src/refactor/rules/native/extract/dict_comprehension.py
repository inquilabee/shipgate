"""Native rule for ``dict-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class DictComprehensionRule(PatternNativeRule):
    rule_id = "dict-comprehension"
    kind_value = "refactor"
    summary = "Dict comprehension"
    needle = "dict_comprehension"
    replacement = "Review dictionary pattern for dict-comprehension"
