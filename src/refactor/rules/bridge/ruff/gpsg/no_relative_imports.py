"""Bridge: no-relative-imports → Ruff TID252 (ban all relative imports)."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class NoRelativeImportsBridge(RuffBridge):
    rule_id = "no-relative-imports"
    kind = RuleKind.SUGGESTION
    summary = "Always use absolute imports instead of relative imports"
    message = "Always use absolute imports instead of relative imports"
    delegates_to = "TID252"
    ruff_config = ('lint.flake8-tidy-imports.ban-relative-imports="all"',)
