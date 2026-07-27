"""Native rule for ``hoist-statement-from-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistStatementFromIfRule(PatternNativeRule):
    rule_id = "hoist-statement-from-if"
    kind_value = "refactor"
    summary = "Hoist statement from if"
    needle = "hoist_statement_from_if"
    replacement = "Review conditional pattern for hoist-statement-from-if"
