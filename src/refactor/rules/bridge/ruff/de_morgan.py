"""Bridge rule: de-morgan delegates to Ruff SIM220."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class DeMorganBridge(RuffBridge):
    rule_id = "de-morgan"
    kind = RuleKind.REFACTOR
    summary = "De Morgan"
    message = "Simplify expressions that combine a value with its negation"
    delegates_to = "SIM220"
