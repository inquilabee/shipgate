"""Inventory stub: Sourcery path-read delegates to Ruff PTH123."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class PathReadBridge(RuffBridge):
    rule_id = "path-read"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff PTH123 (not enforced here)."
    delegates_to = "PTH123"
