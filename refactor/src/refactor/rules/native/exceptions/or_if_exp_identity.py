"""Native rule for ``or-if-exp-identity``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class OrIfExpIdentityRule(PatternNativeRule):
    rule_id = "or-if-exp-identity"
    kind_value = "refactor"
    summary = "Or if exp identity"
    needle = "or_if_exp_identity"
    replacement = "Review conditional pattern for or-if-exp-identity"
