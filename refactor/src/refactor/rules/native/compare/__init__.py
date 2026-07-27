"""Native Sourcery parity rules."""

from __future__ import annotations

from refactor.rules.native.compare.aware_datetime_for_utc import AwareDatetimeForUtcRule
from refactor.rules.native.compare.dont_import_test_modules import DontImportTestModulesRule
from refactor.rules.native.compare.hoist_statement_from_loop import HoistStatementFromLoopRule
from refactor.rules.native.compare.merge_comparisons import MergeComparisonsRule
from refactor.rules.native.compare.move_assign import MoveAssignRule
from refactor.rules.native.compare.remove_duplicate_set_key import RemoveDuplicateSetKeyRule
from refactor.rules.native.compare.remove_unnecessary_else import RemoveUnnecessaryElseRule
from refactor.rules.native.compare.simplify_len_comparison import SimplifyLenComparisonRule
from refactor.rules.native.compare.ternary_to_if_expression import TernaryToIfExpressionRule
from refactor.rules.native.compare.use_join import UseJoinRule

RULES = (
    AwareDatetimeForUtcRule(),
    DontImportTestModulesRule(),
    HoistStatementFromLoopRule(),
    MergeComparisonsRule(),
    MoveAssignRule(),
    RemoveDuplicateSetKeyRule(),
    RemoveUnnecessaryElseRule(),
    SimplifyLenComparisonRule(),
    TernaryToIfExpressionRule(),
    UseJoinRule(),
)
