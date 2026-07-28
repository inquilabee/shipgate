"""Bridge rule: do-not-use-bare-except delegates to Ruff E722."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class DoNotUseBareExceptBridge(RuffBridge):
    rule_id = "do-not-use-bare-except"
    kind = RuleKind.SUGGESTION
    summary = "Do not use bare except"
    message = "Catch a specific exception type instead of using a bare except"
    delegates_to = "E722"
