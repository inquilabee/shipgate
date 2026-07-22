"""Branded ID types with validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_id(value: str, *, kind: str = "id") -> str:
    if not value:
        raise ValueError(f"{kind} must not be empty")
    if "/" in value or "\\" in value or " " in value:
        raise ValueError(f"invalid {kind}: {value!r}")
    if value != value.lower():
        raise ValueError(f"{kind} must be lowercase: {value!r}")
    if not ID_PATTERN.match(value):
        raise ValueError(f"invalid {kind}: {value!r}")
    return value


@dataclass(frozen=True)
class RunnableId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", validate_id(self.value, kind="runnable id"))


@dataclass(frozen=True)
class SuiteId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", validate_id(self.value, kind="suite id"))


@dataclass(frozen=True)
class CheckId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", validate_id(self.value, kind="check id"))


@dataclass(frozen=True)
class CapabilityId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", validate_id(self.value, kind="capability id"))
