"""Bridge rule: avoid-builtin-shadow delegates to Ruff A001."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class AvoidBuiltinShadowBridge(RuffBridge):
    rule_id = "avoid-builtin-shadow"
    kind = RuleKind.COMMENT
    summary = "Avoid builtin shadow"
    message = "Do not assign names that shadow Python builtins"
    delegates_to = "A001"
