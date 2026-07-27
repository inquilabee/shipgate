from refactor.rules.native.anydict.str_prefix_suffix import StrPrefixSuffixRule
from refactor.rules.native.builtins.use_len import UseLenRule
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
