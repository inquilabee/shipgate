"""Inventory stub: Sourcery list-literal delegates to Ruff C408."""

from __future__ import annotations

from typing import TYPE_CHECKING

from refactor.protocol import Hit, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence


class ListLiteralBridge:
    rule_id = "list-literal"
    kind = RuleKind.REFACTOR
    summary = "Delegates to Ruff C408 (not enforced here)."
    safe_apply = False
    delegates_to = "C408"

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self, source, path
        return []

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None
