"""Native rule for ``class-method-first-arg-name``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ClassMethodFirstArgNameRule(PatternNativeRule):
    rule_id = "class-method-first-arg-name"
    kind_value = "refactor"
    summary = "Class method first arg name"
    needle = "class_method_first_arg_name"
    replacement = "Review method extraction pattern for class-method-first-arg-name"
