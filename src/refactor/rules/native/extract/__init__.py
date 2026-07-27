"""Native refactor rules."""

from __future__ import annotations

from refactor.rules.native.extract.dict_comprehension import DictComprehensionRule
from refactor.rules.native.extract.hoist_statement_from_if import (
    HoistStatementFromIfRule,
)
from refactor.rules.native.extract.merge_assign_and_aug_assign import (
    MergeAssignAndAugAssignRule,
)
from refactor.rules.native.extract.missing_dict_items import MissingDictItemsRule
from refactor.rules.native.extract.remove_duplicate_key import RemoveDuplicateKeyRule
from refactor.rules.native.extract.remove_unnecessary_cast import (
    RemoveUnnecessaryCastRule,
)
from refactor.rules.native.extract.simplify_generator import SimplifyGeneratorRule
from refactor.rules.native.extract.switch import SwitchRule
from refactor.rules.native.extract.use_itertools_product import UseItertoolsProductRule

RULES = (
    DictComprehensionRule(),
    HoistStatementFromIfRule(),
    MergeAssignAndAugAssignRule(),
    MissingDictItemsRule(),
    RemoveDuplicateKeyRule(),
    RemoveUnnecessaryCastRule(),
    SimplifyGeneratorRule(),
    SwitchRule(),
    UseItertoolsProductRule(),
)
