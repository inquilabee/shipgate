"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.stdlib.dataframe_append_to_concat import DataframeAppendToConcatRule
from refactor.rules.native.stdlib.hoist_loop_from_if import HoistLoopFromIfRule
from refactor.rules.native.stdlib.list_comprehension import ListComprehensionRule
from refactor.rules.native.stdlib.merge_repeated_ifs import MergeRepeatedIfsRule
from refactor.rules.native.stdlib.remove_dict_items import RemoveDictItemsRule
from refactor.rules.native.stdlib.remove_redundant_exception import RemoveRedundantExceptionRule
from refactor.rules.native.stdlib.simplify_dictionary_update import SimplifyDictionaryUpdateRule
from refactor.rules.native.stdlib.swap_if_expression import SwapIfExpressionRule
from refactor.rules.native.stdlib.use_file_iterator import UseFileIteratorRule

RULES = (
    DataframeAppendToConcatRule(),
    HoistLoopFromIfRule(),
    ListComprehensionRule(),
    MergeRepeatedIfsRule(),
    RemoveDictItemsRule(),
    RemoveRedundantExceptionRule(),
    SimplifyDictionaryUpdateRule(),
    SwapIfExpressionRule(),
    UseFileIteratorRule(),
)
