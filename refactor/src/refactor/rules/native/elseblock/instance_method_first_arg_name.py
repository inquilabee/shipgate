"""Native rule for ``instance-method-first-arg-name``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class InstanceMethodFirstArgNameRule(PatternNativeRule):
    rule_id = "instance-method-first-arg-name"
    kind_value = "refactor"
    summary = "Instance method first arg name"
    needle = "instance_method_first_arg_name"
    replacement = "Review method extraction pattern for instance-method-first-arg-name"
