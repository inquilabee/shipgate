"""Native rule for ``replace-interpolation-with-fstring``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReplaceInterpolationWithFstringRule(PatternNativeRule):
    rule_id = "replace-interpolation-with-fstring"
    kind_value = "refactor"
    summary = "Replace interpolation with fstring"
    needle = "replace_interpolation_with_fstring"
    replacement = "Review string pattern for replace-interpolation-with-fstring"
