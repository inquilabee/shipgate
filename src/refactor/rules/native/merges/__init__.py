"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.merges.chain_compares import ChainComparesRule
from refactor.rules.native.merges.extract_duplicate_method import (
    ExtractDuplicateMethodRule,
)
from refactor.rules.native.merges.inline_variable import InlineVariableRule
from refactor.rules.native.merges.merge_duplicate_blocks import MergeDuplicateBlocksRule
from refactor.rules.native.merges.no_conditionals_in_tests import (
    NoConditionalsInTestsRule,
)
from refactor.rules.native.merges.remove_none_from_default_get import (
    RemoveNoneFromDefaultGetRule,
)
from refactor.rules.native.merges.replace_apply_with_method_call import (
    ReplaceApplyWithMethodCallRule,
)
from refactor.rules.native.merges.simplify_single_exception_tuple import (
    SimplifySingleExceptionTupleRule,
)
from refactor.rules.native.merges.use import UseRule
from refactor.rules.native.merges.use_or_for_fallback import UseOrForFallbackRule

RULES = (
    ChainComparesRule(),
    ExtractDuplicateMethodRule(),
    InlineVariableRule(),
    MergeDuplicateBlocksRule(),
    NoConditionalsInTestsRule(),
    RemoveNoneFromDefaultGetRule(),
    ReplaceApplyWithMethodCallRule(),
    SimplifySingleExceptionTupleRule(),
    UseRule(),
    UseOrForFallbackRule(),
)
