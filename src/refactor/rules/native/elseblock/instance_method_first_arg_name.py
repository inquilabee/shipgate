"""Native rule for ``instance-method-first-arg-name``."""

from __future__ import annotations

from refactor.rules.native.stmt_base import ClassFunctionFirstArgRule


class InstanceMethodFirstArgNameRule(ClassFunctionFirstArgRule):
    rule_id = "instance-method-first-arg-name"
    summary = "Instance method first arg name"
    message = "Name instance method first argument self"
    expected_arg_name = "self"
