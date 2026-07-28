from __future__ import annotations

from refactor.registry import RULES


def test_bridges_registered() -> None:
    bridges = [rule for rule in RULES if hasattr(rule, "delegates_to")]
    assert len(bridges) >= 9
    for bridge in bridges:
        delegates_to = getattr(bridge, "delegates_to", None)
        assert isinstance(delegates_to, str)
        assert delegates_to
        assert bridge.detect("x = 1\n", "sample.py") == []
        assert bridge.safe_apply is False
