"""Native rule for ``remove-redundant-path-exists``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantPathExistsRule(PatternNativeRule):
    rule_id = "remove-redundant-path-exists"
    kind_value = "refactor"
    summary = "Remove redundant path exists"
    needle = "remove_redundant_path_exists"
    replacement = "Review Sourcery pattern for remove-redundant-path-exists"
