from refactor.rules.native.builtins.default_get import DefaultGetRule

BEFORE = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d[key] if key in d else 0
    return value
"""

AFTER = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d.get(key, 0)
    return value
"""


def test_detect_emits_suggestion() -> None:
    rule = DefaultGetRule()
    hits = rule.detect(BEFORE, "sample.py")
    assert len(hits) == 1
    assert hits[0].rule_id == "default-get"
    assert hits[0].suggestion is not None
    assert "d.get(" in hits[0].suggestion.after


def test_apply_round_trip() -> None:
    rule = DefaultGetRule()
    hits = rule.detect(BEFORE, "sample.py")
    rewritten = rule.apply(BEFORE, hits)
    assert rewritten == AFTER
    assert rule.detect(rewritten or "", "sample.py") == []


def test_default_get_apply_fixes_all_occurrences() -> None:
    before = "a = d[k] if k in d else 0\nb = d[k] if k in d else 0\n"
    after = "a = d.get(k, 0)\nb = d.get(k, 0)\n"
    rule = DefaultGetRule()
    hits = rule.detect(before, "x.py")
    assert len(hits) == 2
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "x.py") == []
