from refactor.rules.native.anydict.str_prefix_suffix import StrPrefixSuffixRule
from refactor.rules.native.builtins.use_len import UseLenRule
from refactor.rules.native.compare.hoist_statement_from_loop import (
    HoistStatementFromLoopRule,
)
from refactor.rules.native.elseblock.class_extract_method import ClassExtractMethodRule
from refactor.rules.native.elseblock.extract_method import ExtractMethodRule
from refactor.rules.native.elseblock.no_loop_in_tests import NoLoopInTestsRule
from refactor.rules.native.hoist.introduce_default_else import IntroduceDefaultElseRule
from refactor.rules.native.hoist.use_assigned_variable import UseAssignedVariableRule
from refactor.rules.native.merges.no_conditionals_in_tests import (
    NoConditionalsInTestsRule,
)
from refactor.rules.native.redundancy.simplify_constant_sum import (
    SimplifyConstantSumRule,
)
from refactor.rules.native.syntax.remove_redundant_pass import RemoveRedundantPassRule


def test_use_len_skips_attribute_chains() -> None:
    rule = UseLenRule()
    assert not rule.detect("if len(reader.pages) == 0:\n    pass\n", "x.py")
    hits = rule.detect("if len(items) == 0:\n    pass\n", "x.py")
    assert len(hits) == 1


def test_remove_redundant_pass_keeps_abstract_docstring_stub() -> None:
    rule = RemoveRedundantPassRule()
    source = 'class Base:\n    def hook(self):\n        """Override me."""\n        pass\n'
    assert not rule.detect(source, "x.py")
    assert rule.apply(source, []) is None


def test_remove_redundant_pass_still_clears_after_real_stmt() -> None:
    rule = RemoveRedundantPassRule()
    before = "def f():\n    x = 1\n    pass\n"
    hits = rule.detect(before, "x.py")
    assert len(hits) == 1
    assert rule.apply(before, hits) == "def f():\n    x = 1\n"


def test_simplify_constant_sum_rewrites_sum_one_with_filter() -> None:
    rule = SimplifyConstantSumRule()
    source = "total = sum(1 for item in items if item.ready)\n"
    hits = rule.detect(source, "x.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "sum(item.ready for item in items)" in hits[0].suggestion.after


def test_simplify_constant_sum_skips_unfiltered_sum() -> None:
    rule = SimplifyConstantSumRule()
    assert not rule.detect("total = sum(1 for item in items)\n", "x.py")


def test_use_assigned_variable_reuses_repeated_expression() -> None:
    rule = UseAssignedVariableRule()
    source = (
        "def total(wardrobe):\n"
        "    for item in wardrobe:\n"
        "        count = wardrobe[item]\n"
        "        add_to_total(wardrobe[item])\n"
    )
    hits = rule.detect(source, "x.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "add_to_total(count)" in hits[0].suggestion.after


def test_use_assigned_variable_reuses_aliased_self() -> None:
    rule = UseAssignedVariableRule()
    source = (
        "class Example:\n    def detect(self):\n        _ = self\n        return self.rule_id\n"
    )
    hits = rule.detect(source, "x.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "return _.rule_id" in hits[0].suggestion.after


def test_str_prefix_suffix_accepts_non_decimal_slice_lengths() -> None:
    rule = StrPrefixSuffixRule()
    hits = rule.detect('ok = value[:0x3] == "abc"\nend = value[-0o3:] == "xyz"\n', "x.py")
    assert len(hits) == 2
    assert hits[0].suggestion is not None
    assert "startswith" in hits[0].suggestion.after
    assert hits[1].suggestion is not None
    assert "endswith" in hits[1].suggestion.after


def test_test_only_rules_skip_production_paths() -> None:
    assert not NoConditionalsInTestsRule().detect("if ready:\n    assert ready\n", "src/app.py")
    assert not NoLoopInTestsRule().detect("for case in cases:\n    assert case\n", "src/app.py")


def test_test_only_rules_still_detect_test_paths() -> None:
    condition_hits = NoConditionalsInTestsRule().detect(
        "if ready:\n    assert ready\n",
        "tests/test_app.py",
    )
    loop_hits = NoLoopInTestsRule().detect(
        "for case in cases:\n    assert case\n",
        "tests/test_app.py",
    )
    assert len(condition_hits) == 1
    assert len(loop_hits) == 1


def test_introduce_default_else_requires_default_assignment_pattern() -> None:
    rule = IntroduceDefaultElseRule()
    assert not rule.detect("if ready:\n    run()\n", "x.py")
    hits = rule.detect("value = fallback\nif ready:\n    value = result\n", "x.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "else:\n    value = fallback" in hits[0].suggestion.after


def test_placeholder_extract_rules_are_silent_by_default() -> None:
    function_source = "def run():\n    prepare()\n    execute()\n    finish()\n"
    class_source = (
        "class Example:\n    def run(self):\n"
        "        prepare()\n        execute()\n        finish()\n"
    )
    assert not ExtractMethodRule().detect(function_source, "x.py")
    assert not ClassExtractMethodRule().detect(class_source, "x.py")


def test_unsafe_loop_hoist_is_silent_by_default() -> None:
    rule = HoistStatementFromLoopRule()
    accumulator_source = (
        "worst = 0\nfor req in requests:\n    code = run(req)\n    worst = max(worst, code)\n"
    )
    return_source = (
        "for policy in policies:\n"
        "    if policy.matches(item):\n"
        "        return policy\n"
        "    return None\n"
    )
    assert not rule.detect(accumulator_source, "x.py")
    assert not rule.detect(return_source, "x.py")


def test_use_assigned_variable_skips_constant_literals() -> None:
    rule = UseAssignedVariableRule()
    source = (
        "class Example:\n"
        '    rule_id = "demo"\n'
        "    safe_apply = True\n"
        "    def run(self):\n"
        "        value = None\n"
        "        if other is None:\n"
        "            return self.rule_id\n"
    )
    assert not rule.detect(source, "x.py")


def test_use_assigned_variable_skips_impure_call_alias() -> None:
    rule = UseAssignedVariableRule()
    source = (
        "def elapsed(start):\n    start = time.monotonic()\n    return time.monotonic() - start\n"
    )
    assert not rule.detect(source, "x.py")


def test_use_assigned_variable_skips_assignment_targets() -> None:
    rule = UseAssignedVariableRule()
    source = (
        "def update(run, started_at):\n"
        "    duration_ms = run.duration_ms\n"
        "    if run.finished_at is not None:\n"
        "        duration_ms = 1\n"
        "        run.duration_ms = duration_ms\n"
    )
    assert not rule.detect(source, "x.py")
