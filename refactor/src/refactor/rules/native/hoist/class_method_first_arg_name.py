"""Native rule for ``class-method-first-arg-name``."""

from __future__ import annotations

from refactor.rules.native.stmt_base import ClassFunctionFirstArgRule


class ClassMethodFirstArgNameRule(ClassFunctionFirstArgRule):
    rule_id = "class-method-first-arg-name"
    summary = "Class method first arg name"
    message = "Name class method first argument cls"
    expected_arg_name = "cls"
    required_decorator = "classmethod"
