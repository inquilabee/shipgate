"""Canonical report schema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "shipgate.report.v1"


@dataclass(frozen=True)
class FindingLocation:
    path: str
    line: int | None = None
    column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"path": self.path}
        if self.line is not None:
            result["line"] = self.line
        if self.column is not None:
            result["column"] = self.column
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FindingLocation:
        return cls(
            path=str(data["path"]),
            line=data.get("line"),
            column=data.get("column"),
        )


@dataclass(frozen=True)
class Finding:
    check_id: str
    rule_id: str
    severity: str
    message: str
    location: FindingLocation | None = None
    report_path: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "check_id": self.check_id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.location is not None:
            result["location"] = self.location.to_dict()
        if self.report_path is not None:
            result["report_path"] = self.report_path
        if self.extra:
            result["extra"] = dict(self.extra)
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Finding:
        loc = data.get("location")
        return cls(
            check_id=str(data["check_id"]),
            rule_id=str(data["rule_id"]),
            severity=str(data["severity"]),
            message=str(data["message"]),
            location=FindingLocation.from_dict(loc) if loc else None,
            report_path=data.get("report_path"),
            extra=dict(data.get("extra", {})),
        )


@dataclass(frozen=True)
class CheckReport:
    check_id: str
    tool_id: str
    status: str
    exit_code: int
    findings: tuple[Finding, ...] = ()
    stdout_path: str | None = None
    stderr_path: str | None = None
    extra: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "check_id": self.check_id,
            "tool_id": self.tool_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "findings": [f.to_dict() for f in self.findings],
        }
        if self.stdout_path is not None:
            result["stdout_path"] = self.stdout_path
        if self.stderr_path is not None:
            result["stderr_path"] = self.stderr_path
        if self.extra:
            result["extra"] = dict(self.extra)
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CheckReport:
        return cls(
            check_id=str(data["check_id"]),
            tool_id=str(data["tool_id"]),
            status=str(data["status"]),
            exit_code=int(data["exit_code"]),
            findings=tuple(Finding.from_dict(f) for f in data.get("findings", [])),
            stdout_path=data.get("stdout_path"),
            stderr_path=data.get("stderr_path"),
            extra=dict(data.get("extra", {})),
        )


@dataclass(frozen=True)
class RunReport:
    run_id: str
    suite: str | None
    mode: str
    status: str
    reports: tuple[CheckReport, ...] = ()
    report_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "suite": self.suite,
            "mode": self.mode,
            "status": self.status,
            "reports": [r.to_dict() for r in self.reports],
        }
        if self.report_path is not None:
            result["report_path"] = self.report_path
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RunReport:
        return cls(
            run_id=str(data["run_id"]),
            suite=data.get("suite"),
            mode=str(data["mode"]),
            status=str(data["status"]),
            reports=tuple(CheckReport.from_dict(r) for r in data.get("reports", [])),
            report_path=data.get("report_path"),
        )


def to_dict(obj: object) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()  # type: ignore[union-attr]
    return asdict(obj)  # type: ignore[arg-type]
