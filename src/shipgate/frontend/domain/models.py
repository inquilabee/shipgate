"""Domain models for the report server."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FindingCategory(StrEnum):
    CODE = "code"
    TOOL = "tool"


@dataclass
class RunSummaryRecord:
    finding_count: int
    tool_failure_count: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_check_id: dict[str, int] = field(default_factory=dict)
    by_check_status: dict[str, str] = field(default_factory=dict)
    by_rule_id: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "finding_count": self.finding_count,
            "tool_failure_count": self.tool_failure_count,
            "by_severity": dict(self.by_severity),
            "by_check_id": dict(self.by_check_id),
            "by_check_status": dict(self.by_check_status),
            "by_rule_id": dict(self.by_rule_id),
        }

    @classmethod
    def from_dict(cls, data: dict) -> RunSummaryRecord:
        return cls(
            finding_count=int(data["finding_count"]),
            tool_failure_count=int(data.get("tool_failure_count", 0)),
            by_severity=dict(data.get("by_severity", {})),
            by_check_id=dict(data.get("by_check_id", {})),
            by_check_status={
                str(key): str(value) for key, value in dict(data.get("by_check_status", {})).items()
            },
            by_rule_id={
                str(key): int(value) for key, value in dict(data.get("by_rule_id", {})).items()
            },
        )


@dataclass
class FindingRecord:
    id: str
    run_id: str
    check_id: str
    tool_id: str
    rule_id: str
    severity: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    docs_url: str | None = None
    suggested_commands: list[str] = field(default_factory=list)
    category: FindingCategory = FindingCategory.CODE


@dataclass
class RunRecord:
    id: str
    branch: str
    suite_id: str
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    worktree_path: str | None = None
    error_message: str | None = None
    current_check_id: str | None = None
    checks_completed: int = 0
    checks_total: int = 0
    summary: RunSummaryRecord | None = None
