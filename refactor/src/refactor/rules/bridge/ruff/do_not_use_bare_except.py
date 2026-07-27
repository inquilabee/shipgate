"""Inventory stub: Sourcery do-not-use-bare-except delegates to Ruff E722."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class DoNotUseBareExceptBridge(RuffBridge):
    rule_id = "do-not-use-bare-except"
    kind = RuleKind.SUGGESTION
    summary = "Delegates to Ruff E722 (not enforced here)."
    delegates_to = "E722"
