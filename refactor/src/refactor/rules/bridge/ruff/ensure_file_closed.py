"""Inventory stub: Sourcery ensure-file-closed delegates to Ruff SIM115."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class EnsureFileClosedBridge(RuffBridge):
    rule_id = "ensure-file-closed"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff SIM115 (not enforced here)."
    delegates_to = "SIM115"
