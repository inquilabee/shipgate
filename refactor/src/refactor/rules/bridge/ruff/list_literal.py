"""Inventory stub: Sourcery list-literal delegates to Ruff C408."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class ListLiteralBridge(RuffBridge):
    rule_id = "list-literal"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff C408 (not enforced here)."
    delegates_to = "C408"
