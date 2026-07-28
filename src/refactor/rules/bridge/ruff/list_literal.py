"""Bridge rule: list-literal delegates to Ruff C408."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class ListLiteralBridge(RuffBridge):
    rule_id = "list-literal"
    kind = RuleKind.REFACTOR
    summary = "List literal"
    message = "Prefer empty collection literals over list(), dict(), or tuple() calls"
    delegates_to = "C408"
