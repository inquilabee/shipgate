"""Explicit rule registry (no magic auto-discovery)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from refactor.rules.bridge.ruff.list_literal import ListLiteralBridge
from refactor.rules.native.builtins.default_get import DefaultGetRule
from refactor.rules.native.builtins.default_mutable_arg import DefaultMutableArgRule
from refactor.rules.native.builtins.identity_comprehension import IdentityComprehensionRule
from refactor.rules.native.builtins.min_max_identity import MinMaxIdentityRule
from refactor.rules.native.builtins.use_len import UseLenRule
from refactor.rules.native.syntax.aug_assign import AugAssignRule
from refactor.rules.native.syntax.bin_op_identity import BinOpIdentityRule
from refactor.rules.native.syntax.boolean_if_exp_identity import BooleanIfExpIdentityRule
from refactor.rules.native.syntax.collection_into_set import CollectionIntoSetRule
from refactor.rules.native.syntax.control.for_index_replacement import (
    ForIndexReplacementRule,
)
from refactor.rules.native.syntax.control.inline_immediately_returned_variable import (
    InlineImmediatelyReturnedVariableRule,
)
from refactor.rules.native.syntax.control.merge_nested_ifs import MergeNestedIfsRule
from refactor.rules.native.syntax.control.remove_unreachable_code import (
    RemoveUnreachableCodeRule,
)
from refactor.rules.native.syntax.control.use_next import UseNextRule
from refactor.rules.native.syntax.control.yield_from import YieldFromRule
from refactor.rules.native.syntax.dict_literal import DictLiteralRule
from refactor.rules.native.syntax.none_compare import NoneCompareRule
from refactor.rules.native.syntax.remove_redundant_pass import RemoveRedundantPassRule
from refactor.rules.native.syntax.simplify_boolean_comparison import (
    SimplifyBooleanComparisonRule,
)
from refactor.rules.native.syntax.tuple_literal import TupleLiteralRule

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

RULES: tuple[RefactorRule, ...] = (
    DefaultGetRule(),
    DictLiteralRule(),
    TupleLiteralRule(),
    RemoveRedundantPassRule(),
    UseLenRule(),
    MinMaxIdentityRule(),
    AugAssignRule(),
    NoneCompareRule(),
    BooleanIfExpIdentityRule(),
    SimplifyBooleanComparisonRule(),
    MergeNestedIfsRule(),
    InlineImmediatelyReturnedVariableRule(),
    UseNextRule(),
    IdentityComprehensionRule(),
    ForIndexReplacementRule(),
    CollectionIntoSetRule(),
    DefaultMutableArgRule(),
    RemoveUnreachableCodeRule(),
    YieldFromRule(),
    BinOpIdentityRule(),
    ListLiteralBridge(),
)
