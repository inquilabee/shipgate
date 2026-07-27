"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.elseblock.class_extract_method import ClassExtractMethodRule
from refactor.rules.native.elseblock.extract_method import ExtractMethodRule
from refactor.rules.native.elseblock.instance_method_first_arg_name import (
    InstanceMethodFirstArgNameRule,
)
from refactor.rules.native.elseblock.merge_else_if_into_elif import MergeElseIfIntoElifRule
from refactor.rules.native.elseblock.no_loop_in_tests import NoLoopInTestsRule
from refactor.rules.native.elseblock.remove_pass_body import RemovePassBodyRule
from refactor.rules.native.elseblock.replace_apply_with_numpy_operation import (
    ReplaceApplyWithNumpyOperationRule,
)
from refactor.rules.native.elseblock.simplify_string_len_comparison import (
    SimplifyStringLenComparisonRule,
)
from refactor.rules.native.elseblock.use_any import UseAnyRule
from refactor.rules.native.elseblock.use_string_remove_affix import UseStringRemoveAffixRule

RULES = (
    ClassExtractMethodRule(),
    ExtractMethodRule(),
    InstanceMethodFirstArgNameRule(),
    MergeElseIfIntoElifRule(),
    NoLoopInTestsRule(),
    RemovePassBodyRule(),
    ReplaceApplyWithNumpyOperationRule(),
    SimplifyStringLenComparisonRule(),
    UseAnyRule(),
    UseStringRemoveAffixRule(),
)
