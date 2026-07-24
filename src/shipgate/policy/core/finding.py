"""Canonical finding shape for policy gate reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FindingLocation:
    file: str
    line: int | None = None

    def to_dict(self) -> dict[str, str | int]:
        payload: dict[str, str | int] = {"file": self.file}
        if self.line is not None:
            payload["line"] = self.line
        return payload


@dataclass(frozen=True, slots=True)
class PolicyFinding:
    rule_id: str
    message: str
    severity: str = "error"
    location: FindingLocation | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.location is not None:
            payload["location"] = self.location.to_dict()
        return payload
