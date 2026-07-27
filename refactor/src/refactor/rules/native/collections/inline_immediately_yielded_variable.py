"""Native rule for ``inline-immediately-yielded-variable``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class InlineImmediatelyYieldedVariableRule(PatternNativeRule):
    rule_id = "inline-immediately-yielded-variable"
    kind_value = "refactor"
    summary = "Inline immediately yielded variable"
    needle = "inline_immediately_yielded_variable"
    replacement = "Review Sourcery pattern for inline-immediately-yielded-variable"
