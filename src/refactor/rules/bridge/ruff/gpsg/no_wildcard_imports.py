"""Bridge: no-wildcard-imports → Ruff F403."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class NoWildcardImportsBridge(RuffBridge):
    rule_id = "no-wildcard-imports"
    kind = RuleKind.SUGGESTION
    summary = "Do not use wildcard imports"
    message = "Do not use wildcard imports"
    delegates_to = "F403"
