from __future__ import annotations

from refactor.rules.native.compare.dont_import_test_modules import (
    DontImportTestModulesRule,
)
from refactor.rules.native.redundancy.lift_return_into_if import LiftReturnIntoIfRule
from refactor.rules.native.redundancy.reintroduce_else import ReintroduceElseRule
from refactor.rules.native.strings.remove_redundant_continue import (
    RemoveRedundantContinueRule,
)


def test_body_sequence_rules_populate_hit_locations() -> None:
    reintroduce_hit = ReintroduceElseRule().detect(
        "def f(failed):\n    if failed:\n        return None\n    recover()\n",
        "sample.py",
    )[0]
    lift_hit = LiftReturnIntoIfRule().detect(
        "def f(failed):\n    if failed:\n        return None\n    return recover()\n",
        "sample.py",
    )[0]
    assert reintroduce_hit.location.line == 2
    assert reintroduce_hit.location.column == 4
    assert lift_hit.location.line == 2
    assert lift_hit.location.column == 4


def test_body_cleanup_rules_populate_hit_locations() -> None:
    hit = RemoveRedundantContinueRule().detect(
        "for item in items:\n    process(item)\n    continue\n",
        "sample.py",
    )[0]
    assert hit.location.line == 3
    assert hit.location.column == 4


def test_dont_import_test_modules_skips_test_paths() -> None:
    source = "from tests.unit.support import helper\n"
    rule = DontImportTestModulesRule()
    assert rule.detect(source, "src/pkg/module.py")
    assert not rule.detect(source, "tests/unit/test_sample.py")
