"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.pandas.dict_assign_update_to_union import (
    DictAssignUpdateToUnionRule,
)
from refactor.rules.native.pandas.hoist_similar_statement_from_if import (
    HoistSimilarStatementFromIfRule,
)
from refactor.rules.native.pandas.max_min_default import MaxMinDefaultRule
from refactor.rules.native.pandas.method import MethodRule
from refactor.rules.native.pandas.remove_duplicate_dict_key import (
    RemoveDuplicateDictKeyRule,
)
from refactor.rules.native.pandas.remove_redundant_path_exists import (
    RemoveRedundantPathExistsRule,
)
from refactor.rules.native.pandas.simplify_fstring_formatting import (
    SimplifyFstringFormattingRule,
)
from refactor.rules.native.pandas.swap_variable import SwapVariableRule
from refactor.rules.native.pandas.use_isna import UseIsnaRule

RULES = (
    DictAssignUpdateToUnionRule(),
    HoistSimilarStatementFromIfRule(),
    MaxMinDefaultRule(),
    MethodRule(),
    RemoveDuplicateDictKeyRule(),
    RemoveRedundantPathExistsRule(),
    SimplifyFstringFormattingRule(),
    SwapVariableRule(),
    UseIsnaRule(),
)
