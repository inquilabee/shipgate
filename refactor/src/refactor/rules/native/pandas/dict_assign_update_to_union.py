"""Native rule for ``dict-assign-update-to-union``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class DictAssignUpdateToUnionRule(PatternNativeRule):
    rule_id = "dict-assign-update-to-union"
    kind_value = "refactor"
    summary = "Dict assign update to union"
    needle = "dict_assign_update_to_union"
    replacement = "Review dictionary pattern for dict-assign-update-to-union"
