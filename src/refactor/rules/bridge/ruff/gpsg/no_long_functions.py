"""Bridge: no-long-functions → Ruff PLR0915 with max-statements=40."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class NoLongFunctionsBridge(RuffBridge):
    rule_id = "no-long-functions"
    kind = RuleKind.SUGGESTION
    summary = "Functions should be less than 40 statements"
    message = "Functions should be less than 40 statements"
    delegates_to = "PLR0915"
    ruff_config = ("lint.pylint.max-statements=40",)
