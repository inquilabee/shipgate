"""Native Sourcery parity rules."""

from __future__ import annotations

from refactor.rules.native.redundancy.convert_any_to_in import ConvertAnyToInRule
from refactor.rules.native.redundancy.hoist_if_from_if import HoistIfFromIfRule
from refactor.rules.native.redundancy.lift_return_into_if import LiftReturnIntoIfRule
from refactor.rules.native.redundancy.merge_list_extend import MergeListExtendRule
from refactor.rules.native.redundancy.reintroduce_else import ReintroduceElseRule
from refactor.rules.native.redundancy.remove_redundant_except_handler import (
    RemoveRedundantExceptHandlerRule,
)
from refactor.rules.native.redundancy.simplify_constant_sum import SimplifyConstantSumRule
from refactor.rules.native.redundancy.swap_if_else_branches import SwapIfElseBranchesRule
from refactor.rules.native.redundancy.use_dictionary_union import UseDictionaryUnionRule

RULES = (
    ConvertAnyToInRule(),
    HoistIfFromIfRule(),
    LiftReturnIntoIfRule(),
    MergeListExtendRule(),
    ReintroduceElseRule(),
    RemoveRedundantExceptHandlerRule(),
    SimplifyConstantSumRule(),
    SwapIfElseBranchesRule(),
    UseDictionaryUnionRule(),
)
