"""Native rule for ``str-prefix-suffix``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class StrPrefixSuffixRule(PatternNativeRule):
    rule_id = "str-prefix-suffix"
    kind_value = "refactor"
    summary = "Str prefix suffix"
    needle = "str_prefix_suffix"
    replacement = "Review string pattern for str-prefix-suffix"
