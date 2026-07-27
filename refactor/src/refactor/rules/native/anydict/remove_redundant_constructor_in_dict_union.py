"""Native rule for ``remove-redundant-constructor-in-dict-union``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantConstructorInDictUnionRule(PatternNativeRule):
    rule_id = "remove-redundant-constructor-in-dict-union"
    kind_value = "refactor"
    summary = "Remove redundant constructor in dict union"
    needle = "remove_redundant_constructor_in_dict_union"
    replacement = "Review dictionary pattern for remove-redundant-constructor-in-dict-union"
