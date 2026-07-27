"""Shared pattern-backed native rules for Sourcery parity."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from refactor.cst_util import make_hit, noop_apply
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


KIND_BY_VALUE = {kind.value: kind for kind in RuleKind}


class PatternNativeRule:
    rule_id: ClassVar[str]
    kind_value: ClassVar[str] = "refactor"
    summary: ClassVar[str]
    needle: ClassVar[str]
    replacement: ClassVar[str]
    safe_apply: ClassVar[bool] = False

    @property
    def kind(self) -> RuleKind:
        return KIND_BY_VALUE.get(self.kind_value, RuleKind.REFACTOR)

    def detect(self, source: str, path: str) -> list[Hit]:
        if not self.needle or self.needle not in source:
            return []
        return [
            make_hit(
                rule_id=self.rule_id,
                message=self.summary,
                path=path,
                before=self.needle,
                after=self.replacement,
            ),
        ]

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return noop_apply(source, hits)
