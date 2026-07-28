"""Overview page context builders."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from shipgate.baseline import load_baseline
from shipgate.frontend.domain.baseline import (
    fingerprint_from_record,
    fingerprints_from_report,
    fixed_finding_rows,
    fixed_fingerprints,
    severity_deltas_vs_baseline,
)
from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunRecord,
    RunSummaryRecord,
)
from shipgate.frontend.web.security import ui_token_from_env

if TYPE_CHECKING:
    from fastapi import Request

    from shipgate.domain.reports import RunReport
    from shipgate.frontend.storage.sqlite import SqliteStorage

FindingFingerprint = tuple[str, str, str, int | None, str]


def overview_context(
    request: Request, storage: SqliteStorage, run_id: str | None
) -> dict[str, Any]:
    run, run_missing = resolve_overview_run(storage, run_id)
    latest = storage.list_runs(limit=1)
    baseline = load_baseline(request.app.state.primary_root)
    baseline_fps: set[FindingFingerprint] = (
        fingerprints_from_report(baseline) if baseline else set()
    )
    context: dict[str, Any] = {
        "request": request,
        "run": run,
        "run_missing": run_missing,
        "latest_run": latest[0] if latest else None,
        "previous": None,
        "deltas": None,
        "baseline_deltas": None,
        "hotspots": [],
        "by_check": [],
        "tool_failures": [],
        "gate_status": None,
        "baseline_new_count": None,
        "baseline_fixed_count": None,
        "baseline_fixed_rows": [],
        "csrf_token": request.app.state.csrf_token,
        "ui_token": ui_token_from_env() or "",
    }
    if run is None:
        return context
    previous = storage.previous_completed_run(branch=run.branch, before_run_id=run.id)
    context |= {
        "previous": previous,
        "deltas": severity_deltas(run.summary, previous.summary if previous else None),
    }
    attach_baseline_context(context, run, baseline)
    code_findings = storage.list_findings(run.id, category=FindingCategory.CODE)
    context |= {
        "hotspots": file_hotspots(code_findings),
        "by_check": by_check_rows(run.summary),
    }
    context |= {
        "tool_failures": storage.list_findings(run.id, category=FindingCategory.TOOL),
        "gate_status": gate_status(run),
    }
    attach_baseline_finding_counts(context, baseline, baseline_fps, code_findings)
    return context


def attach_baseline_context(
    context: dict[str, Any], run: RunRecord, baseline: RunReport | None
) -> None:
    baseline_sev = baseline_severity_counts(baseline)
    if run.summary and baseline_sev is not None:
        context["baseline_deltas"] = severity_deltas_vs_baseline(
            run.summary.by_severity, baseline_sev
        )


def baseline_severity_counts(baseline: RunReport | None) -> dict[str, int] | None:
    if baseline is None or not baseline.reports:
        return None
    baseline_sev: dict[str, int] = {}
    for finding in (finding for check in baseline.reports for finding in check.findings):
        baseline_sev[finding.severity] = baseline_sev.get(finding.severity, 0) + 1
    return baseline_sev


def attach_baseline_finding_counts(
    context: dict[str, Any],
    baseline: RunReport | None,
    baseline_fps: set[FindingFingerprint],
    code_findings: list[FindingRecord],
) -> None:
    if not baseline_fps:
        return
    current_fps = {fingerprint_from_record(finding) for finding in code_findings}
    fixed_fps = fixed_fingerprints(baseline_fps, current_fps)
    context |= {
        "baseline_new_count": sum(fingerprint not in baseline_fps for fingerprint in current_fps),
        "baseline_fixed_count": len(fixed_fps),
    }
    if baseline is not None:
        context["baseline_fixed_rows"] = fixed_finding_rows(baseline, fixed_fps)


def gate_status(run: RunRecord) -> str | None:
    if run.summary is None:
        return None
    if gate_statuses := {
        check_id: status
        for check_id, status in run.summary.by_check_status.items()
        if check_id.startswith("gate.")
    }:
        return "failed" if "failed" in gate_statuses.values() else "passed"
    return "passed" if run.status.value == "succeeded" else "failed"


def resolve_overview_run(
    storage: SqliteStorage, run_id: str | None
) -> tuple[RunRecord | None, bool]:
    if run_id:
        run = storage.get_run(run_id)
        return (None, True) if run is None else (run, False)
    runs = storage.list_runs(limit=1)
    return (runs[0] if runs else None), False


def severity_deltas(
    current: RunSummaryRecord | None,
    previous: RunSummaryRecord | None,
) -> dict[str, int] | None:
    if current is None or previous is None:
        return None
    keys = ("error", "warning", "info")
    cur = current.by_severity
    prev = previous.by_severity
    return {
        "total": current.finding_count - previous.finding_count,
        **{key: cur.get(key, 0) - prev.get(key, 0) for key in keys},
    }


def file_hotspots(findings: list[FindingRecord], *, limit: int = 10) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for finding in findings:
        if finding.file:
            counts[finding.file] += 1
    return [{"file": path, "count": count} for path, count in counts.most_common(limit)]


def by_check_rows(summary: RunSummaryRecord | None) -> list[dict[str, Any]]:
    return (
        []
        if summary is None
        else [
            {"check_id": check_id, "count": count}
            for check_id, count in sorted(
                summary.by_check_id.items(), key=lambda item: (-item[1], item[0])
            )
            if count > 0
        ]
    )


def overview_payload(storage: SqliteStorage, primary_root, run_id: str) -> dict[str, Any] | None:
    """JSON-serializable overview aggregates (same math as the HTML overview)."""
    from pathlib import Path

    run = storage.get_run(run_id)
    if run is None:
        return None
    baseline = load_baseline(Path(primary_root))
    baseline_fps: set[FindingFingerprint] = (
        fingerprints_from_report(baseline) if baseline else set()
    )
    previous = storage.previous_completed_run(branch=run.branch, before_run_id=run.id)
    code_findings = storage.list_findings(run.id, category=FindingCategory.CODE)
    payload: dict[str, Any] = {
        "run_id": run.id,
        "branch": run.branch,
        "suite_id": run.suite_id,
        "status": run.status.value,
        "by_severity": dict(run.summary.by_severity) if run.summary else {},
        "finding_count": run.summary.finding_count if run.summary else 0,
        "tool_failure_count": run.summary.tool_failure_count if run.summary else 0,
        "deltas": severity_deltas(run.summary, previous.summary if previous else None),
        "hotspots": file_hotspots(code_findings),
        "by_check": by_check_rows(run.summary),
        "gate_status": gate_status(run),
        "baseline_new_count": None,
        "baseline_fixed_count": None,
        "baseline_deltas": None,
    }
    baseline_sev = baseline_severity_counts(baseline)
    if run.summary and baseline_sev is not None:
        payload["baseline_deltas"] = severity_deltas_vs_baseline(
            run.summary.by_severity, baseline_sev
        )
    baseline_new_count, baseline_fixed_count = baseline_finding_count_pair(
        baseline_fps, code_findings
    )
    payload |= {
        "baseline_new_count": baseline_new_count,
        "baseline_fixed_count": baseline_fixed_count,
    }
    return payload


def baseline_finding_count_pair(
    baseline_fps: set[FindingFingerprint], code_findings: list[FindingRecord]
) -> tuple[int | None, int | None]:
    if not baseline_fps:
        return None, None
    current_fps = {fingerprint_from_record(finding) for finding in code_findings}
    fixed_fps = fixed_fingerprints(baseline_fps, current_fps)
    new_count = sum(fingerprint not in baseline_fps for fingerprint in current_fps)
    return new_count, len(fixed_fps)


def trends_payload(
    storage: SqliteStorage, *, branch: str | None, limit: int = 20
) -> list[dict[str, Any]]:
    rows = [
        {
            "run_id": run.id,
            "started_at": run.started_at.isoformat(),
            "finding_count": run.summary.finding_count if run.summary else 0,
            "by_severity": dict(run.summary.by_severity) if run.summary else {},
            "status": run.status.value,
        }
        for run in storage.list_runs(limit=limit, branch=branch)
    ]
    rows.reverse()
    return rows
