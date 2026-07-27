from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class RuleKind(Enum):
    REFACTOR = "refactor"
    SUGGESTION = "suggestion"
    COMMENT = "comment"


@dataclass(frozen=True)
class Location:
    path: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True)
class Suggestion:
    before: str
    after: str
    message: str | None = None


@dataclass(frozen=True)
class Hit:
    rule_id: str
    message: str
    location: Location
    suggestion: Suggestion | None = None
    extra: Mapping[str, object] = field(default_factory=dict)


class RefactorRule(Protocol):
    rule_id: str
    kind: RuleKind
    summary: str
    safe_apply: bool

    def detect(self, source: str, path: str) -> list[Hit]: ...

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None: ...
