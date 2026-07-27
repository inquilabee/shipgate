from refactor.rules.native.anydict.str_prefix_suffix import StrPrefixSuffixRule
from refactor.rules.native.builtins.use_len import UseLenRule
from refactor.rules.native.compare.hoist_statement_from_loop import HoistStatementFromLoopRule
from refactor.rules.native.elseblock.class_extract_method import ClassExtractMethodRule
from refactor.rules.native.elseblock.extract_method import ExtractMethodRule
from refactor.rules.native.elseblock.no_loop_in_tests import NoLoopInTestsRule
from refactor.rules.native.hoist.introduce_default_else import IntroduceDefaultElseRule
from refactor.rules.native.merges.no_conditionals_in_tests import NoConditionalsInTestsRule
from refactor.rules.native.redundancy.simplify_constant_sum import SimplifyConstantSumRule
from refactor.rules.native.syntax.remove_redundant_pass import RemoveRedundantPassRule


def test_use_len_skips_attribute_chains() -> None:
    rule = UseLenRule()
    assert rule.detect("if len(reader.pages) == 0:\n    pass\n", "x.py") == []
    hits = rule.detect("if len(items) == 0:\n    pass\n", "x.py")
    assert len(hits) == 1


def test_remove_redundant_pass_keeps_abstract_docstring_stub() -> None:
    rule = RemoveRedundantPassRule()
    source = 'class Base:\n    def hook(self):\n        """Override me."""\n        pass\n'
    assert rule.detect(source, "x.py") == []
    assert rule.apply(source, []) is None


def test_remove_redundant_pass_still_clears_after_real_stmt() -> None:
    rule = RemoveRedundantPassRule()
    before = "def f():\n    x = 1\n    pass\n"
    hits = rule.detect(before, "x.py")
    assert len(hits) == 1
    assert rule.apply(before, hits) == "def f():\n    x = 1\n"


def test_simplify_constant_sum_accepts_python_integer_bases() -> None:
    rule = SimplifyConstantSumRule()
    source = "a = 1_000 + 2\nb = 0b10 + 0o10\nc = 0x10 - 0b1\n"
    hits = rule.detect(source, "x.py")
    after_values = [hit.suggestion.after for hit in hits if hit.suggestion is not None]
    assert "1002" in after_values[0]
    assert "10" in after_values[1]
    assert "15" in after_values[2]


def test_str_prefix_suffix_accepts_non_decimal_slice_lengths() -> None:
    rule = StrPrefixSuffixRule()
    hits = rule.detect('ok = value[:0x3] == "abc"\nend = value[-0o3:] == "xyz"\n', "x.py")
    assert len(hits) == 2
    assert hits[0].suggestion is not None
    assert "startswith" in hits[0].suggestion.after
    assert hits[1].suggestion is not None
    assert "endswith" in hits[1].suggestion.after


def test_test_only_rules_skip_production_paths() -> None:
    assert NoConditionalsInTestsRule().detect("if ready:\n    assert ready\n", "src/app.py") == []
    assert NoLoopInTestsRule().detect("for case in cases:\n    assert case\n", "src/app.py") == []


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
    assert rule.detect("if ready:\n    run()\n", "x.py") == []
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
    assert ExtractMethodRule().detect(function_source, "x.py") == []
    assert ClassExtractMethodRule().detect(class_source, "x.py") == []


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
    assert rule.detect(accumulator_source, "x.py") == []
    assert rule.detect(return_source, "x.py") == []
