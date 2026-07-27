"""Native rule for ``comprehension-to-generator``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ComprehensionToGeneratorRule(PatternNativeRule):
    rule_id = "comprehension-to-generator"
    kind_value = "refactor"
    summary = "Comprehension to generator"
    needle = "comprehension_to_generator"
    replacement = "Review Sourcery pattern for comprehension-to-generator"
