"""Native rule for ``use-contextlib-suppress``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseContextlibSuppressRule(PatternNativeRule):
    rule_id = "use-contextlib-suppress"
    kind_value = "refactor"
    summary = "Use contextlib suppress"
    needle = "use_contextlib_suppress"
    replacement = "Review Sourcery pattern for use-contextlib-suppress"
