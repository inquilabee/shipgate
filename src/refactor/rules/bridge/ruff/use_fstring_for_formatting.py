"""Bridge rule: use-fstring-for-formatting delegates to Ruff UP031."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class UseFstringForFormattingBridge(RuffBridge):
    rule_id = "use-fstring-for-formatting"
    kind = RuleKind.REFACTOR
    summary = "Use fstring for formatting"
    message = "Prefer f-strings or str.format() over printf-style formatting"
    delegates_to = "UP031"
