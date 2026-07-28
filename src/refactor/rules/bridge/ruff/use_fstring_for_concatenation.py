"""Bridge rule: use-fstring-for-concatenation delegates to Ruff UP032."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class UseFstringForConcatenationBridge(RuffBridge):
    rule_id = "use-fstring-for-concatenation"
    kind = RuleKind.REFACTOR
    summary = "Use fstring for concatenation"
    message = "Prefer f-strings over str.format() calls"
    delegates_to = "UP032"
