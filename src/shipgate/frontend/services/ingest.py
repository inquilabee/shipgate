"""Ingest RunReport data into report-server storage."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
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
# Threshold / policy breaches are code findings even when a tool exits non-zero.
CODE_FAILURE_MARKERS = ("too many duplicates",)


def empty_ingest_buckets() -> tuple[
    list[FindingRecord],
    dict[str, int],
    dict[str, int],
    dict[str, str],
    dict[str, int],
]:
    return [], {}, {}, {}, {}


def ingest_run_report(
    storage: Storage,
    run_id: str,
    report: RunReport,
    project_root: Path,
) -> RunSummaryRecord:
    findings, by_severity, by_check_id, by_check_status, by_rule_id = empty_ingest_buckets()
    for check in report.reports:
        ingest_check(
            check,
            run_id,
            project_root,
            findings,
            by_severity,
            by_check_id,
            by_check_status,
            by_rule_id,
        )
    summary = summarize(findings, by_severity, by_check_id, by_check_status, by_rule_id)
    storage.replace_findings(run_id, findings)
    return summary


def ingest_check_into_storage(
    storage: Storage,
    run_id: str,
    check: CheckReport,
    project_root: Path,
) -> RunSummaryRecord:
    """Merge one completed check into SQLite (mid-run live update)."""
    findings, by_severity, by_check_id, by_check_status, by_rule_id = empty_ingest_buckets()
    ingest_check(
        check,
        run_id,
        project_root,
        findings,
        by_severity,
        by_check_id,
        by_check_status,
        by_rule_id,
    )
    storage.upsert_check_findings(run_id, check.check_id, findings)
    all_findings = storage.list_findings(run_id)
    merged_sev: dict[str, int] = {}
    merged_check: dict[str, int] = {}
    merged_status: dict[str, str] = {}
    merged_rules: dict[str, int] = {}
    run = storage.get_run(run_id)
    if run and run.summary:
        merged_status.update(run.summary.by_check_status)
    merged_status.update(by_check_status)
    for finding in all_findings:
        if finding.category == FindingCategory.CODE:
            merged_sev[finding.severity] = merged_sev.get(finding.severity, 0) + 1
            merged_check[finding.check_id] = merged_check.get(finding.check_id, 0) + 1
            merged_rules[finding.rule_id] = merged_rules.get(finding.rule_id, 0) + 1
        elif finding.check_id not in merged_check:
            merged_check[finding.check_id] = 0
    for check_id, status in by_check_status.items():
        if status in {"passed", "skipped"} and check_id not in merged_check:
            merged_check[check_id] = 0
    return summarize(all_findings, merged_sev, merged_check, merged_status, merged_rules)


def ingest_check(
    check: CheckReport,
    run_id: str,
    project_root: Path,
    findings: list[FindingRecord],
    by_severity: dict[str, int],
    by_check_id: dict[str, int],
    by_check_status: dict[str, str],
    by_rule_id: dict[str, int],
) -> None:
    by_check_status[check.check_id] = check.status
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
            by_rule_id[record.rule_id] = by_rule_id.get(record.rule_id, 0) + 1
    by_check_id[check.check_id] = check_code


def summarize(
    findings: list[FindingRecord],
    by_severity: dict[str, int],
    by_check_id: dict[str, int],
    by_check_status: dict[str, str],
    by_rule_id: dict[str, int],
) -> RunSummaryRecord:
    code_count = sum(1 for f in findings if f.category == FindingCategory.CODE)
    tool_count = sum(1 for f in findings if f.category == FindingCategory.TOOL)
    return RunSummaryRecord(
        finding_count=code_count,
        tool_failure_count=tool_count,
        by_severity=by_severity,
        by_check_id=by_check_id,
        by_check_status=by_check_status,
        by_rule_id=by_rule_id,
    )


def is_tool_failure_fields(*, rule_id: str, message: str, has_location: bool) -> bool:
    message_l = message.lower()
    if rule_id == "threshold" or any(marker in message_l for marker in CODE_FAILURE_MARKERS):
        return False
    if rule_id in TOOL_RULE_IDS:
        return True
    if has_location:
        return False
    return any(marker in message_l for marker in TOOL_MESSAGE_MARKERS)


def is_tool_failure(finding: Finding) -> bool:
    return is_tool_failure_fields(
        rule_id=finding.rule_id,
        message=finding.message,
        has_location=finding.location is not None,
    )


def is_tool_failure_record(finding: FindingRecord) -> bool:
    return is_tool_failure_fields(
        rule_id=finding.rule_id,
        message=finding.message,
        has_location=finding.file is not None,
    )


def repair_misclassified_tool_findings(storage: Storage) -> int:
    """Reclassify stored threshold/policy breaches that were ingested as tool failures."""
    from shipgate.frontend.storage.base import MAX_RUNS

    repaired = 0
    for run in storage.list_runs(limit=MAX_RUNS):
        tool_findings = storage.list_findings(run.id, category=FindingCategory.TOOL)
        if not tool_findings:
            continue
        changed = False
        all_findings = storage.list_findings(run.id)
        by_id = {finding.id: finding for finding in all_findings}
        for finding in tool_findings:
            if is_tool_failure_record(finding):
                continue
            finding.category = FindingCategory.CODE
            by_id[finding.id] = finding
            changed = True
            repaired += 1
        if not changed:
            continue
        refreshed = list(by_id.values())
        storage.replace_findings(run.id, refreshed)
        summary = summarize_from_records(refreshed, run.summary)
        storage.update_run(run.id, summary=summary)
    return repaired


def summarize_from_records(
    findings: list[FindingRecord],
    previous: RunSummaryRecord | None,
) -> RunSummaryRecord:
    by_severity: dict[str, int] = {}
    by_check_id: dict[str, int] = {}
    by_rule_id: dict[str, int] = {}
    by_check_status = dict(previous.by_check_status) if previous else {}
    for finding in findings:
        if finding.category != FindingCategory.CODE:
            if finding.check_id not in by_check_id:
                by_check_id[finding.check_id] = 0
            continue
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        by_check_id[finding.check_id] = by_check_id.get(finding.check_id, 0) + 1
        by_rule_id[finding.rule_id] = by_rule_id.get(finding.rule_id, 0) + 1
    for check_id, status in by_check_status.items():
        if status in {"passed", "skipped"} and check_id not in by_check_id:
            by_check_id[check_id] = 0
    return summarize(findings, by_severity, by_check_id, by_check_status, by_rule_id)


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


def docs_from_extra(extra: Mapping[str, object] | None) -> tuple[str | None, list[str]]:
    if not extra:
        return None, []
    docs_url = extra.get("docs_url")
    commands_raw = extra.get("suggested_commands")
    raw_map = as_str_object_map(extra.get("raw"))
    if raw_map is not None:
        docs_url = docs_url or docs_url_from_raw(raw_map)
        if commands_raw is None:
            raw_commands = raw_map.get("suggested_commands")
            if isinstance(raw_commands, list):
                commands_raw = raw_commands
    return normalize_docs_url(docs_url), normalize_suggested_commands(commands_raw)


def as_str_object_map(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}


def docs_url_from_raw(raw: Mapping[str, object]) -> str | None:
    for key in ("url", "more_info", "documentation_url", "help_uri"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_docs_url(docs_url: object) -> str | None:
    if isinstance(docs_url, str) and docs_url.strip():
        return docs_url.strip()
    return None


def normalize_suggested_commands(commands_raw: object) -> list[str]:
    if not isinstance(commands_raw, list):
        return []
    return [str(item) for item in commands_raw if str(item).strip()]


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
    docs_url, suggested_commands = docs_from_extra(finding.extra)
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
        docs_url=docs_url,
        suggested_commands=suggested_commands,
        category=category,
    )
