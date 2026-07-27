"""Native rule for ``chain-compares``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ChainComparesRule(PatternNativeRule):
    rule_id = "chain-compares"
    kind_value = "refactor"
    summary = "Chain compares"
    needle = "chain_compares"
    replacement = "Review comparison pattern for chain-compares"
