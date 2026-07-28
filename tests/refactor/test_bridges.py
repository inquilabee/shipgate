from __future__ import annotations

from refactor.protocol import ApplyMode
from refactor.registry import RULES
from refactor.rules.bridge.ruff.avoid_builtin_shadow import AvoidBuiltinShadowBridge
from refactor.rules.bridge.ruff.list_literal import ListLiteralBridge


def test_bridges_registered() -> None:
    bridges = [rule for rule in RULES if hasattr(rule, "delegates_to")]
    assert len(bridges) >= 9
    assert all(
        isinstance(getattr(bridge, "delegates_to", None), str)
        and getattr(bridge, "delegates_to", None)
        and bridge.summary
        and getattr(bridge, "message", None)
        and "Delegates to Ruff" not in bridge.summary
        and bridge.apply_mode is ApplyMode.HINT
        for bridge in bridges
    )


def test_avoid_builtin_shadow_detects_via_ruff() -> None:
    rule = AvoidBuiltinShadowBridge()
    hits = rule.detect("list = []\nmax = 1\n", "sample.py")
    assert len(hits) >= 2
    assert all(hit.rule_id == "avoid-builtin-shadow" for hit in hits)
    assert all(hit.message == rule.message for hit in hits)
    assert all(hit.extra.get("ruff_code") == "A001" for hit in hits)
    assert hits[0].location.line is not None


def test_list_literal_detects_and_suggests_via_ruff() -> None:
    rule = ListLiteralBridge()
    source = "values = list()\n"
    hits = rule.detect(source, "sample.py")
    assert len(hits) == 1
    hit = hits[0]
    assert hit.rule_id == "list-literal"
    assert hit.message == rule.message
    assert hit.suggestion is not None
    assert hit.suggestion.before == "list()"
    assert hit.suggestion.after == "[]"


def test_list_literal_apply_rewrites_via_ruff() -> None:
    rule = ListLiteralBridge()
    source = "values = list()\n"
    hits = rule.detect(source, "sample.py")
    rewritten = rule.apply(source, hits)
    assert rewritten == "values = []\n"
