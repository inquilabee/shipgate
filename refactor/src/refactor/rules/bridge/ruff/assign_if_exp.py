"""Inventory stub: Sourcery assign-if-exp delegates to Ruff SIM108."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class AssignIfExpBridge(RuffBridge):
    rule_id = "assign-if-exp"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff SIM108 (not enforced here)."
    delegates_to = "SIM108"
