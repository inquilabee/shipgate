"""Native rule for ``hoist-statement-from-loop``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistStatementFromLoopRule(PatternNativeRule):
    rule_id = "hoist-statement-from-loop"
    kind_value = "refactor"
    summary = "Hoist statement from loop"
    needle = "hoist_statement_from_loop"
    replacement = "Review loop pattern for hoist-statement-from-loop"
