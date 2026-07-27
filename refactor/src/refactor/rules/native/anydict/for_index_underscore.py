"""Native rule for ``for-index-underscore``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ForIndexUnderscoreRule(PatternNativeRule):
    rule_id = "for-index-underscore"
    kind_value = "refactor"
    summary = "For index underscore"
    needle = "for_index_underscore"
    replacement = "Review loop pattern for for-index-underscore"
