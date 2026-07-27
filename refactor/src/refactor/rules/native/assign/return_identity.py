"""Native rule for ``return-identity``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReturnIdentityRule(PatternNativeRule):
    rule_id = "return-identity"
    kind_value = "refactor"
    summary = "Return identity"
    needle = "return_identity"
    replacement = "Review Sourcery pattern for return-identity"
