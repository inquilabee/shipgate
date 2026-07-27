"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.strings.comprehension_to_generator import (
    ComprehensionToGeneratorRule,
)
from refactor.rules.native.strings.guard import GuardRule
from refactor.rules.native.strings.lift_duplicated_conditional import (
    LiftDuplicatedConditionalRule,
)
from refactor.rules.native.strings.merge_list_appends_into_extend import (
    MergeListAppendsIntoExtendRule,
)
from refactor.rules.native.strings.raise_specific_error import RaiseSpecificErrorRule
from refactor.rules.native.strings.remove_redundant_continue import (
    RemoveRedundantContinueRule,
)
from refactor.rules.native.strings.set_comprehension import SetComprehensionRule
from refactor.rules.native.strings.sum_comprehension import SumComprehensionRule
from refactor.rules.native.strings.use_dict_items import UseDictItemsRule

RULES = (
    ComprehensionToGeneratorRule(),
    GuardRule(),
    LiftDuplicatedConditionalRule(),
    MergeListAppendsIntoExtendRule(),
    RaiseSpecificErrorRule(),
    RemoveRedundantContinueRule(),
    SetComprehensionRule(),
    SumComprehensionRule(),
    UseDictItemsRule(),
)
