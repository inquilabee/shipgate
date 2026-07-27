"""Native rule for ``extract-method``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ExtractMethodRule(PatternNativeRule):
    rule_id = "extract-method"
    kind_value = "refactor"
    summary = "Extract method"
    needle = "extract_method"
    replacement = "Review method extraction pattern for extract-method"
