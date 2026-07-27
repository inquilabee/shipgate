"""Native rule for ``replace-apply-with-method-call``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReplaceApplyWithMethodCallRule(PatternNativeRule):
    rule_id = "replace-apply-with-method-call"
    kind_value = "refactor"
    summary = "Replace apply with method call"
    needle = "replace_apply_with_method_call"
    replacement = "Review method extraction pattern for replace-apply-with-method-call"
