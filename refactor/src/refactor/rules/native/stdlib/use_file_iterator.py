"""Native rule for ``use-file-iterator``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseFileIteratorRule(PatternNativeRule):
    rule_id = "use-file-iterator"
    kind_value = "refactor"
    summary = "Use file iterator"
    needle = "use_file_iterator"
    replacement = "Review Sourcery pattern for use-file-iterator"
