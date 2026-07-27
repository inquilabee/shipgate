"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.anydict.compare_via_equals import CompareViaEqualsRule
from refactor.rules.native.anydict.for_index_underscore import ForIndexUnderscoreRule
from refactor.rules.native.anydict.last_if_guard import LastIfGuardRule
from refactor.rules.native.anydict.merge_list_append import MergeListAppendRule
from refactor.rules.native.anydict.raise_from_previous_error import RaiseFromPreviousErrorRule
from refactor.rules.native.anydict.remove_redundant_constructor_in_dict_union import (
    RemoveRedundantConstructorInDictUnionRule,
)
from refactor.rules.native.anydict.return_or_yield_outside_function import (
    ReturnOrYieldOutsideFunctionRule,
)
from refactor.rules.native.anydict.str_prefix_suffix import StrPrefixSuffixRule
from refactor.rules.native.anydict.use_datetime_now_not_today import UseDatetimeNowNotTodayRule

RULES = (
    CompareViaEqualsRule(),
    ForIndexUnderscoreRule(),
    LastIfGuardRule(),
    MergeListAppendRule(),
    RaiseFromPreviousErrorRule(),
    RemoveRedundantConstructorInDictUnionRule(),
    ReturnOrYieldOutsideFunctionRule(),
    StrPrefixSuffixRule(),
    UseDatetimeNowNotTodayRule(),
)
