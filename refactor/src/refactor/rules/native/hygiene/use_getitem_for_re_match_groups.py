"""Native rule for ``use-getitem-for-re-match-groups``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseGetitemForReMatchGroupsRule(PatternNativeRule):
    rule_id = "use-getitem-for-re-match-groups"
    kind_value = "refactor"
    summary = "Use getitem for re match groups"
    needle = "use_getitem_for_re_match_groups"
    replacement = "Review loop pattern for use-getitem-for-re-match-groups"
