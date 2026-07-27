"""Native rule for ``class-extract-method``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ClassExtractMethodRule(PatternNativeRule):
    rule_id = "class-extract-method"
    kind_value = "refactor"
    summary = "Class extract method"
    needle = "class_extract_method"
    replacement = "Review method extraction pattern for class-extract-method"
