"""Native rule for ``equality-identity``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class EqualityIdentityRule(PatternNativeRule):
    rule_id = "equality-identity"
    kind_value = "refactor"
    summary = "Equality identity"
    needle = "equality_identity"
    replacement = "Review comparison pattern for equality-identity"
