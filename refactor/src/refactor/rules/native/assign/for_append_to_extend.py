"""Native rule for ``for-append-to-extend``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ForAppendToExtendRule(PatternNativeRule):
    rule_id = "for-append-to-extend"
    kind_value = "refactor"
    summary = "For append to extend"
    needle = "for_append_to_extend"
    replacement = "Review loop pattern for for-append-to-extend"
