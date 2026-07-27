"""Inventory stub: Sourcery convert-to-enumerate delegates to Ruff SIM113."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class ConvertToEnumerateBridge(RuffBridge):
    rule_id = "convert-to-enumerate"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff SIM113 (not enforced here)."
    delegates_to = "SIM113"
