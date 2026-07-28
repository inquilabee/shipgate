"""Explicit rule registry (no magic auto-discovery)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from refactor.rules.bridge.ruff.avoid_builtin_shadow import AvoidBuiltinShadowBridge
from refactor.rules.bridge.ruff.convert_to_enumerate import ConvertToEnumerateBridge
from refactor.rules.bridge.ruff.de_morgan import DeMorganBridge
from refactor.rules.bridge.ruff.do_not_use_bare_except import DoNotUseBareExceptBridge
from refactor.rules.bridge.ruff.ensure_file_closed import EnsureFileClosedBridge
from refactor.rules.bridge.ruff.gpsg import RULES as GPSG_BRIDGE_RULES
from refactor.rules.bridge.ruff.list_literal import ListLiteralBridge
from refactor.rules.bridge.ruff.path_read import PathReadBridge
from refactor.rules.bridge.ruff.use_fstring_for_concatenation import (
    UseFstringForConcatenationBridge,
)
from refactor.rules.bridge.ruff.use_fstring_for_formatting import (
    UseFstringForFormattingBridge,
)
from refactor.rules.native.anydict import RULES as ANYDICT_RULES
from refactor.rules.native.assign import RULES as ASSIGN_RULES
from refactor.rules.native.builtins.default_get import DefaultGetRule
from refactor.rules.native.builtins.default_mutable_arg import DefaultMutableArgRule
from refactor.rules.native.builtins.identity_comprehension import (
    IdentityComprehensionRule,
)
from refactor.rules.native.builtins.min_max_identity import MinMaxIdentityRule
from refactor.rules.native.builtins.remove_str_from_fstring import (
    RemoveStrFromFstringRule,
)
from refactor.rules.native.builtins.remove_str_from_print import RemoveStrFromPrintRule
from refactor.rules.native.builtins.use_len import UseLenRule
from refactor.rules.native.collections import RULES as COLLECTIONS_RULES
from refactor.rules.native.compare import RULES as COMPARE_RULES
from refactor.rules.native.elseblock import RULES as ELSEBLOCK_RULES
from refactor.rules.native.exceptions import RULES as EXCEPTIONS_RULES
from refactor.rules.native.extract import RULES as EXTRACT_RULES
from refactor.rules.native.gpsg import RULES as GPSG_NATIVE_RULES
from refactor.rules.native.hoist import RULES as HOIST_RULES
from refactor.rules.native.hygiene import RULES as HYGIENE_RULES
from refactor.rules.native.merges import RULES as MERGES_RULES
from refactor.rules.native.pandas import RULES as PANDAS_RULES
from refactor.rules.native.redundancy import RULES as REDUNDANCY_RULES
from refactor.rules.native.stdlib import RULES as STDLIB_RULES
from refactor.rules.native.strings import RULES as STRINGS_RULES
from refactor.rules.native.syntax.aug_assign import AugAssignRule
from refactor.rules.native.syntax.bin_op_identity import BinOpIdentityRule
from refactor.rules.native.syntax.binary.simplify_division import SimplifyDivisionRule
from refactor.rules.native.syntax.binary.square_identity import SquareIdentityRule
from refactor.rules.native.syntax.boolean_if_exp_identity import (
    BooleanIfExpIdentityRule,
)
from refactor.rules.native.syntax.collection_into_set import CollectionIntoSetRule
from refactor.rules.native.syntax.control.for_index_replacement import (
    ForIndexReplacementRule,
)
from refactor.rules.native.syntax.control.inline_immediately_returned_variable import (
    InlineImmediatelyReturnedVariableRule,
)
from refactor.rules.native.syntax.control.merge_nested_ifs import MergeNestedIfsRule
from refactor.rules.native.syntax.control.remove_assert_true import RemoveAssertTrueRule
from refactor.rules.native.syntax.control.remove_unreachable_code import (
    RemoveUnreachableCodeRule,
)
from refactor.rules.native.syntax.control.use_next import UseNextRule
from refactor.rules.native.syntax.control.yield_from import YieldFromRule
from refactor.rules.native.syntax.dict_literal import DictLiteralRule
from refactor.rules.native.syntax.fstring.remove_redundant_fstring import (
    RemoveRedundantFstringRule,
)
from refactor.rules.native.syntax.none_compare import NoneCompareRule
from refactor.rules.native.syntax.range.remove_unit_step_from_range import (
    RemoveUnitStepFromRangeRule,
)
from refactor.rules.native.syntax.range.remove_zero_from_range import (
    RemoveZeroFromRangeRule,
)
from refactor.rules.native.syntax.remove_redundant_pass import RemoveRedundantPassRule
from refactor.rules.native.syntax.simplify_boolean_comparison import (
    SimplifyBooleanComparisonRule,
)
from refactor.rules.native.syntax.subscript.remove_redundant_slice_index import (
    RemoveRedundantSliceIndexRule,
)
from refactor.rules.native.syntax.subscript.simplify_negative_index import (
    SimplifyNegativeIndexRule,
)
from refactor.rules.native.syntax.tuple_literal import TupleLiteralRule

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

GENERATED_RULES = (
    *COMPARE_RULES,
    *COLLECTIONS_RULES,
    *MERGES_RULES,
    *ELSEBLOCK_RULES,
    *HOIST_RULES,
    *EXCEPTIONS_RULES,
    *ASSIGN_RULES,
    *ANYDICT_RULES,
    *STRINGS_RULES,
    *REDUNDANCY_RULES,
    *STDLIB_RULES,
    *HYGIENE_RULES,
    *PANDAS_RULES,
    *EXTRACT_RULES,
)

RULES = cast(
    "tuple[RefactorRule, ...]",
    (
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
        RemoveZeroFromRangeRule(),
        RemoveUnitStepFromRangeRule(),
        RemoveRedundantSliceIndexRule(),
        SimplifyNegativeIndexRule(),
        SquareIdentityRule(),
        SimplifyDivisionRule(),
        RemoveStrFromPrintRule(),
        RemoveStrFromFstringRule(),
        RemoveRedundantFstringRule(),
        RemoveAssertTrueRule(),
        ListLiteralBridge(),
        AvoidBuiltinShadowBridge(),
        DoNotUseBareExceptBridge(),
        UseFstringForConcatenationBridge(),
        UseFstringForFormattingBridge(),
        PathReadBridge(),
        ConvertToEnumerateBridge(),
        DeMorganBridge(),
        EnsureFileClosedBridge(),
        *GENERATED_RULES,
        *GPSG_BRIDGE_RULES,
        *GPSG_NATIVE_RULES,
    ),
)
