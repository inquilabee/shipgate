"""Bridge rule: ensure-file-closed delegates to Ruff SIM115."""

from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge


class EnsureFileClosedBridge(RuffBridge):
    rule_id = "ensure-file-closed"
    kind = RuleKind.REFACTOR
    summary = "Ensure file closed"
    message = "Open files with a context manager so they are closed reliably"
    delegates_to = "SIM115"
