"""Native rule for ``hoist-similar-statement-from-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistSimilarStatementFromIfRule(PatternNativeRule):
    rule_id = "hoist-similar-statement-from-if"
    kind_value = "refactor"
    summary = "Hoist similar statement from if"
    needle = "hoist_similar_statement_from_if"
    replacement = "Review conditional pattern for hoist-similar-statement-from-if"
