"""Native rule for ``simplify-generator``."""

from __future__ import annotations

from refactor.rules.native.strings.comprehension_to_generator import ComprehensionToGeneratorRule


class SimplifyGeneratorRule(ComprehensionToGeneratorRule):
    rule_id = "simplify-generator"
    summary = "Simplify generator"
    message = "Pass a generator expression instead of a list comprehension"
