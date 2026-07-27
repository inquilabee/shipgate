"""Native rule for ``remove-none-from-default-get``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveNoneFromDefaultGetRule(PatternNativeRule):
    rule_id = "remove-none-from-default-get"
    kind_value = "refactor"
    summary = "Remove none from default get"
    needle = "remove_none_from_default_get"
    replacement = "Review Sourcery pattern for remove-none-from-default-get"
