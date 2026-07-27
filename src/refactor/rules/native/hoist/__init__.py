"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.hoist.class_method_first_arg_name import (
    ClassMethodFirstArgNameRule,
)
from refactor.rules.native.hoist.flatten_nested_try import FlattenNestedTryRule
from refactor.rules.native.hoist.introduce_default_else import IntroduceDefaultElseRule
from refactor.rules.native.hoist.merge_except_handler import MergeExceptHandlerRule
from refactor.rules.native.hoist.non_equal_comparison import NonEqualComparisonRule
from refactor.rules.native.hoist.remove_pass_elif import RemovePassElifRule
from refactor.rules.native.hoist.replace_dict_items_with_values import (
    ReplaceDictItemsWithValuesRule,
)
from refactor.rules.native.hoist.simplify_substring_search import (
    SimplifySubstringSearchRule,
)
from refactor.rules.native.hoist.use_assigned_variable import UseAssignedVariableRule
from refactor.rules.native.hoist.useless_else_on_loop import UselessElseOnLoopRule

RULES = (
    ClassMethodFirstArgNameRule(),
    FlattenNestedTryRule(),
    IntroduceDefaultElseRule(),
    MergeExceptHandlerRule(),
    NonEqualComparisonRule(),
    RemovePassElifRule(),
    ReplaceDictItemsWithValuesRule(),
    SimplifySubstringSearchRule(),
    UseAssignedVariableRule(),
    UselessElseOnLoopRule(),
)
