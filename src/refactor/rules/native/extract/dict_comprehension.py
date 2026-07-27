"""Native rule for ``dict-comprehension``."""

from __future__ import annotations

from refactor.rules.native.exceptions.collection_builtin_to_comprehension import (
    CollectionBuiltinToComprehensionRule,
)


class DictComprehensionRule(CollectionBuiltinToComprehensionRule):
    rule_id = "dict-comprehension"
    summary = "Dict comprehension"
    message = "Use a dict comprehension instead of dict() around a generator"
