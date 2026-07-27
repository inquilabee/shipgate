from refactor.rules.native.builtins.use_len import UseLenRule
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
