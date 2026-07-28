"""Bridge: map-lambda-to-generator → Ruff C417."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class MapLambdaToGeneratorBridge(RuffBridge):
    rule_id = "map-lambda-to-generator"
    kind = RuleKind.SUGGESTION
    summary = "Replace mapping a lambda with a generator expression"
    message = "Replace mapping a lambda with a generator expression"
    delegates_to = "C417"
