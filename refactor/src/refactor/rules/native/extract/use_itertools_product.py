"""Native rule for ``use-itertools-product``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseItertoolsProductRule(PatternNativeRule):
    rule_id = "use-itertools-product"
    kind_value = "refactor"
    summary = "Use itertools product"
    needle = "use_itertools_product"
    replacement = "Review Sourcery pattern for use-itertools-product"
