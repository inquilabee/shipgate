"""Native rule for ``replace-apply-with-numpy-operation``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReplaceApplyWithNumpyOperationRule(PatternNativeRule):
    rule_id = "replace-apply-with-numpy-operation"
    kind_value = "refactor"
    summary = "Replace apply with numpy operation"
    needle = "replace_apply_with_numpy_operation"
    replacement = "Review pandas pattern for replace-apply-with-numpy-operation"
