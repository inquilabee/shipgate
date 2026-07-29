"""Shared Ruff-delegating bridge rules.

Each subclass declares an external refactor ``rule_id`` and the Ruff code(s) it
delegates to. Detection runs ``ruff check --select=<codes>`` on the source;
optional apply runs ``ruff check --fix`` for the same selection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from refactor.protocol import ApplyMode, Hit, Location
from refactor.ruff_invoke import (
    location_row_column,
    run_ruff_check,
    run_ruff_fix,
    suggestion_from_diagnostic,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from refactor.protocol import RuleKind


class RuffBridge:
    rule_id: ClassVar[str]
    kind: ClassVar[RuleKind]
    summary: ClassVar[str]
    message: ClassVar[str]
    delegates_to: ClassVar[str]
    apply_mode = ApplyMode.HINT
    ruff_config: ClassVar[tuple[str, ...]] = ()

    def detect(self, source: str, path: str) -> list[Hit]:
        codes = self.select_codes()
        diagnostics = run_ruff_check(source, path, codes, config=self.ruff_config or None)
        return [
            self.diagnostic_to_hit(source, path, diagnostic)
            for diagnostic in diagnostics
            if str(diagnostic.get("code") or "") in codes
        ]

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        if not hits:
            return None
        path = hits[0].location.path
        fixed = run_ruff_fix(source, path, self.select_codes(), config=self.ruff_config or None)
        return None if fixed is None or fixed == source else fixed

    def select_codes(self) -> frozenset[str]:
        return frozenset(code.strip() for code in self.delegates_to.split(",") if code.strip())

    def diagnostic_to_hit(
        self,
        source: str,
        path: str,
        diagnostic: Mapping[str, object],
    ) -> Hit:
        row, column = location_row_column(diagnostic.get("location"))
        ruff_message = str(diagnostic.get("message") or self.message)
        return Hit(
            rule_id=self.rule_id,
            message=self.message,
            location=Location(path=path, line=row, column=column),
            suggestion=suggestion_from_diagnostic(source, diagnostic),
            extra={
                "ruff_code": str(diagnostic.get("code") or ""),
                "ruff_message": ruff_message,
            },
        )
