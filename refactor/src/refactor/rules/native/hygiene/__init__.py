"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.hygiene.del_comprehension import DelComprehensionRule
from refactor.rules.native.hygiene.hoist_repeated_if_condition import HoistRepeatedIfConditionRule
from refactor.rules.native.hygiene.low_code_quality import LowCodeQualityRule
from refactor.rules.native.hygiene.merge_set_add import MergeSetAddRule
from refactor.rules.native.hygiene.remove_dict_keys import RemoveDictKeysRule
from refactor.rules.native.hygiene.remove_redundant_if import RemoveRedundantIfRule
from refactor.rules.native.hygiene.simplify_empty_collection_comparison import (
    SimplifyEmptyCollectionComparisonRule,
)
from refactor.rules.native.hygiene.swap_nested_ifs import SwapNestedIfsRule
from refactor.rules.native.hygiene.use_getitem_for_re_match_groups import (
    UseGetitemForReMatchGroupsRule,
)

RULES = (
    DelComprehensionRule(),
    HoistRepeatedIfConditionRule(),
    LowCodeQualityRule(),
    MergeSetAddRule(),
    RemoveDictKeysRule(),
    RemoveRedundantIfRule(),
    SimplifyEmptyCollectionComparisonRule(),
    SwapNestedIfsRule(),
    UseGetitemForReMatchGroupsRule(),
)
