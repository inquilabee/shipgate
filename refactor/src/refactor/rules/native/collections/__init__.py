"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.collections.break_or_continue_outside_loop import (
    BreakOrContinueOutsideLoopRule,
)
from refactor.rules.native.collections.equality_identity import EqualityIdentityRule
from refactor.rules.native.collections.inline_immediately_yielded_variable import (
    InlineImmediatelyYieldedVariableRule,
)
from refactor.rules.native.collections.merge_dict_assign import MergeDictAssignRule
from refactor.rules.native.collections.move_assign_in_block import MoveAssignInBlockRule
from refactor.rules.native.collections.remove_empty_nested_block import RemoveEmptyNestedBlockRule
from refactor.rules.native.collections.remove_unused_enumerate import RemoveUnusedEnumerateRule
from refactor.rules.native.collections.simplify_numeric_comparison import (
    SimplifyNumericComparisonRule,
)
from refactor.rules.native.collections.unwrap_iterable_construction import (
    UnwrapIterableConstructionRule,
)
from refactor.rules.native.collections.use_named_expression import UseNamedExpressionRule

RULES = (
    BreakOrContinueOutsideLoopRule(),
    EqualityIdentityRule(),
    InlineImmediatelyYieldedVariableRule(),
    MergeDictAssignRule(),
    MoveAssignInBlockRule(),
    RemoveEmptyNestedBlockRule(),
    RemoveUnusedEnumerateRule(),
    SimplifyNumericComparisonRule(),
    UnwrapIterableConstructionRule(),
    UseNamedExpressionRule(),
)
