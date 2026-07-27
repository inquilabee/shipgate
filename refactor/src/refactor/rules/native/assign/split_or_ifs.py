"""Native rule for ``split-or-ifs``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SplitOrIfsRule(PatternNativeRule):
    rule_id = "split-or-ifs"
    kind_value = "refactor"
    summary = "Split or ifs"
    needle = "split_or_ifs"
    replacement = "Review conditional pattern for split-or-ifs"
