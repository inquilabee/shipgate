"""Bridge: errors-named-error → Ruff N818."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class ErrorsNamedErrorBridge(RuffBridge):
    rule_id = "errors-named-error"
    kind = RuleKind.SUGGESTION
    summary = "Exception names must end in Error"
    message = "Exception names must end in Error"
    delegates_to = "N818"
