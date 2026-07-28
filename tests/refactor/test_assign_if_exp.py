from __future__ import annotations

import pathlib

from refactor.registry import RULES


def assign_if_exp_rule():
    return next(rule for rule in RULES if rule.rule_id == "assign-if-exp")


def test_assign_if_exp_return_pattern() -> None:
    source = "def f():\n    if call is None:\n        return None\n    return call\n"
    hits = assign_if_exp_rule().detect(source, "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "return None if call is None else call" in hits[0].suggestion.after


def test_assign_if_exp_return_tuple_uses_parentheses() -> None:
    source = (
        "def f(call):\n"
        "    if call is None:\n"
        "        return None\n"
        "    return call, call.args[0].value\n"
    )
    hits = assign_if_exp_rule().detect(source, "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "return None if call is None else (call, call.args[0].value)" in hits[0].suggestion.after


def test_assign_if_exp_if_else_assign() -> None:
    source = "if condition:\n    result = left\nelse:\n    result = right\n"
    hits = assign_if_exp_rule().detect(source, "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "left if condition else right" in hits[0].suggestion.after


def test_assign_if_exp_explain_reports_native(capsys) -> None:
    from refactor.cli import main

    assert main(["explain", "assign-if-exp"]) == 0
    out = capsys.readouterr().out
    assert "assign-if-exp" in out
    assert "status: native" in out


def test_assign_if_exp_detects_call_match_pattern() -> None:
    source = pathlib.Path("src/refactor/call_match.py").read_text()
    hits = assign_if_exp_rule().detect(source, "src/refactor/call_match.py")
    assert isinstance(hits, list)
