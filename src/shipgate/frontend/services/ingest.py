"""Ingest RunReport data into report-server storage."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunSummaryRecord,
)
from shipgate.paths import normalize_finding_path

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.reports import CheckReport, Finding, RunReport
    from shipgate.frontend.storage.base import Storage

TOOL_RULE_IDS = frozenset({"exit_code", "TOOL_EXIT", "setup", "parser_error"})
TOOL_MESSAGE_MARKERS = (
    "modulenotfounderror",
    "no module named",
    "executable not found",
    "failed to install",
    "failed to parse tool output",
)


def ingest_run_report(
    storage: Storage,
    run_id: str,
    report: RunReport,
    project_root: Path,
) -> RunSummaryRecord:
    findings: list[FindingRecord] = []
    by_severity: dict[str, int] = {}
    by_check_id: dict[str, int] = {}
    for check in report.reports:
        ingest_check(check, run_id, project_root, findings, by_severity, by_check_id)
    summary = summarize(findings, by_severity, by_check_id)
    storage.replace_findings(run_id, findings)
    return summary


def ingest_check(
    check: CheckReport,
    run_id: str,
    project_root: Path,
    findings: list[FindingRecord],
    by_severity: dict[str, int],
    by_check_id: dict[str, int],
) -> None:
    if check.status in {"passed", "skipped"} and not check.findings:
        by_check_id[check.check_id] = 0
        return
    if check.status == "failed" and not check.findings:
        findings.append(
            setup_error_record(run_id=run_id, check_id=check.check_id, message="Check failed")
        )
        by_check_id[check.check_id] = 0
        return
    check_code = 0
    for finding in check.findings:
        record = finding_to_record(
            finding=finding,
            run_id=run_id,
            check_id=check.check_id,
            tool_id=check.tool_id,
            project_root=project_root,
        )
        findings.append(record)
        if record.category == FindingCategory.CODE:
            check_code += 1
            by_severity[record.severity] = by_severity.get(record.severity, 0) + 1
    by_check_id[check.check_id] = check_code


def summarize(
    findings: list[FindingRecord],
    by_severity: dict[str, int],
    by_check_id: dict[str, int],
) -> RunSummaryRecord:
    code_count = sum(1 for f in findings if f.category == FindingCategory.CODE)
    tool_count = sum(1 for f in findings if f.category == FindingCategory.TOOL)
    return RunSummaryRecord(
        finding_count=code_count,
        tool_failure_count=tool_count,
        by_severity=by_severity,
        by_check_id=by_check_id,
    )


def is_tool_failure(finding: Finding) -> bool:
    if finding.rule_id in TOOL_RULE_IDS:
        return True
    if finding.location is not None:
        return False
    message_l = finding.message.lower()
    return any(marker in message_l for marker in TOOL_MESSAGE_MARKERS)


def setup_error_record(*, run_id: str, check_id: str, message: str) -> FindingRecord:
    tool_id = check_id.split(".", 1)[0]
    return FindingRecord(
        id=uuid.uuid4().hex,
        run_id=run_id,
        check_id=check_id,
        tool_id=tool_id,
        rule_id="setup",
        severity="error",
        message=message,
        category=FindingCategory.TOOL,
    )


def finding_to_record(
    *,
    finding: Finding,
    run_id: str,
    check_id: str,
    tool_id: str,
    project_root: Path,
) -> FindingRecord:
    location = finding.location
    category = FindingCategory.TOOL if is_tool_failure(finding) else FindingCategory.CODE
    raw_file = location.path if location else None
    return FindingRecord(
        id=uuid.uuid4().hex,
        run_id=run_id,
        check_id=check_id,
        tool_id=tool_id,
        rule_id=finding.rule_id,
        severity=finding.severity,
        message=finding.message,
        file=normalize_finding_path(raw_file, project_root=project_root),
        line=location.line if location else None,
        column=location.column if location else None,
        category=category,
    )
