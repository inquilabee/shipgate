"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.exceptions.collection_builtin_to_comprehension import (
    CollectionBuiltinToComprehensionRule,
)
from refactor.rules.native.exceptions.flip_comparison import FlipComparisonRule
from refactor.rules.native.exceptions.invert_any_all import InvertAnyAllRule
from refactor.rules.native.exceptions.merge_is_instance import MergeIsInstanceRule
from refactor.rules.native.exceptions.or_if_exp_identity import OrIfExpIdentityRule
from refactor.rules.native.exceptions.remove_redundant_boolean import (
    RemoveRedundantBooleanRule,
)
from refactor.rules.native.exceptions.replace_interpolation_with_fstring import (
    ReplaceInterpolationWithFstringRule,
)
from refactor.rules.native.exceptions.skip_sorted_list_construction import (
    SkipSortedListConstructionRule,
)
from refactor.rules.native.exceptions.use_contextlib_suppress import (
    UseContextlibSuppressRule,
)
from refactor.rules.native.exceptions.while_guard_to_condition import (
    WhileGuardToConditionRule,
)

RULES = (
    CollectionBuiltinToComprehensionRule(),
    FlipComparisonRule(),
    InvertAnyAllRule(),
    MergeIsInstanceRule(),
    OrIfExpIdentityRule(),
    RemoveRedundantBooleanRule(),
    ReplaceInterpolationWithFstringRule(),
    SkipSortedListConstructionRule(),
    UseContextlibSuppressRule(),
    WhileGuardToConditionRule(),
)
