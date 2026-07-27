"""Native rule for ``remove-pass-body``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemovePassBodyRule(PatternNativeRule):
    rule_id = "remove-pass-body"
    kind_value = "refactor"
    summary = "Remove pass body"
    needle = "remove_pass_body"
    replacement = "Review Sourcery pattern for remove-pass-body"
