"""Inventory stub: Sourcery use-fstring-for-formatting delegates to Ruff UP031."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class UseFstringForFormattingBridge(RuffBridge):
    rule_id = "use-fstring-for-formatting"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff UP031 (not enforced here)."
    delegates_to = "UP031"
