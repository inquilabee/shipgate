"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.assign.collection_to_bool import CollectionToBoolRule
from refactor.rules.native.assign.for_append_to_extend import ForAppendToExtendRule
from refactor.rules.native.assign.invert_any_all_body import InvertAnyAllBodyRule
from refactor.rules.native.assign.merge_isinstance import MergeIsinstanceRule
from refactor.rules.native.assign.pandas_avoid_inplace import PandasAvoidInplaceRule
from refactor.rules.native.assign.remove_redundant_condition import (
    RemoveRedundantConditionRule,
)
from refactor.rules.native.assign.return_identity import ReturnIdentityRule
from refactor.rules.native.assign.split_or_ifs import SplitOrIfsRule
from refactor.rules.native.assign.use_count import UseCountRule
from refactor.rules.native.assign.while_to_for import WhileToForRule

RULES = (
    CollectionToBoolRule(),
    ForAppendToExtendRule(),
    InvertAnyAllBodyRule(),
    MergeIsinstanceRule(),
    PandasAvoidInplaceRule(),
    RemoveRedundantConditionRule(),
    ReturnIdentityRule(),
    SplitOrIfsRule(),
    UseCountRule(),
    WhileToForRule(),
)
