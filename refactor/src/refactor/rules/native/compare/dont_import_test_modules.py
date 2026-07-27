"""Native rule for ``dont-import-test-modules``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class DontImportTestModulesRule(PatternNativeRule):
    rule_id = "dont-import-test-modules"
    kind_value = "refactor"
    summary = "Dont import test modules"
    needle = "dont_import_test_modules"
    replacement = "Review Sourcery pattern for dont-import-test-modules"
