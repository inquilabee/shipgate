"""Inventory stub: Sourcery de-morgan delegates to Ruff SIM220."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class DeMorganBridge(RuffBridge):
    rule_id = "de-morgan"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff SIM220 (not enforced here)."
    delegates_to = "SIM220"
