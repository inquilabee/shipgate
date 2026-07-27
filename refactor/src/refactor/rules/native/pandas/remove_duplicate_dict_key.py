"""Native rule for ``remove-duplicate-dict-key``."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.native.extract.remove_duplicate_key import RemoveDuplicateKeyRule


class RemoveDuplicateDictKeyRule(RemoveDuplicateKeyRule):
    rule_id = "remove-duplicate-dict-key"
    kind = RuleKind.SUGGESTION
    summary = "Remove duplicate dict key"
    message = "Remove duplicate dictionary keys that are overwritten later"
