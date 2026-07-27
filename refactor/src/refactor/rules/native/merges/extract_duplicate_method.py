"""Native rule for ``extract-duplicate-method``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ExtractDuplicateMethodRule(PatternNativeRule):
    rule_id = "extract-duplicate-method"
    kind_value = "refactor"
    summary = "Extract duplicate method"
    needle = "extract_duplicate_method"
    replacement = "Review method extraction pattern for extract-duplicate-method"
