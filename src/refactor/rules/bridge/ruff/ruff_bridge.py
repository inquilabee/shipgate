"""Shared noop implementation for Ruff-delegating bridge rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit, RuleKind


class RuffBridge:
    rule_id: ClassVar[str]
    kind: ClassVar[RuleKind]
    summary: ClassVar[str]
    delegates_to: ClassVar[str]
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self, source, path
        return []

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None
