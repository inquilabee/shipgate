from __future__ import annotations

import pathlib

import pytest

from refactor.registry import RULES

# Real project source to scan, as a path that does not depend on the working
# directory. `call_match` started as one module and is a package now, so glob
# it rather than naming a file that a later split can silently invalidate.
CALL_MATCH_DIR = pathlib.Path(__file__).resolve().parents[2] / "src" / "refactor" / "call_match"
CALL_MATCH_MODULES = sorted(CALL_MATCH_DIR.glob("*.py"))


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


def test_call_match_package_has_modules_to_scan() -> None:
    """Guard the parametrization below: an empty glob would pass vacuously."""
    assert CALL_MATCH_MODULES, f"no modules to scan under {CALL_MATCH_DIR}"


@pytest.mark.parametrize("path", CALL_MATCH_MODULES, ids=lambda p: p.name)
def test_assign_if_exp_detects_call_match_pattern(path: pathlib.Path) -> None:
    """Scan real project source, not a synthetic snippet.

    The cases above pin the rewrites; this one is the "survives real code"
    check. Every hit must carry a location pointing into the file it was handed,
    so a rule that mislabels its findings fails here rather than shipping them.
    """
    hits = assign_if_exp_rule().detect(path.read_text(encoding="utf-8"), str(path))
    assert all(hit.rule_id == "assign-if-exp" for hit in hits)
    assert all(hit.location.path == str(path) for hit in hits)
    assert all((hit.location.line or 0) >= 1 for hit in hits)
