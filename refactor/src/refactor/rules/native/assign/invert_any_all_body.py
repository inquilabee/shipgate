"""Native rule for ``invert-any-all-body``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class InvertAnyAllBodyRule(PatternNativeRule):
    rule_id = "invert-any-all-body"
    kind_value = "refactor"
    summary = "Invert any all body"
    needle = "invert_any_all_body"
    replacement = "Review Sourcery pattern for invert-any-all-body"
