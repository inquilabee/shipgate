"""Explicit rule registry (no magic auto-discovery)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from refactor.rules.bridge.list_literal import ListLiteralBridge
from refactor.rules.native.default_get import DefaultGetRule

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

RULES: tuple[RefactorRule, ...] = (
    DefaultGetRule(),
    ListLiteralBridge(),
)
