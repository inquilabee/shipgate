"""Overview page context builders."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from shipgate.baseline import load_baseline
from shipgate.frontend.domain.baseline import (
    fingerprint_from_record,
    fingerprints_from_report,
    severity_deltas_vs_baseline,
)
from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunRecord,
    RunSummaryRecord,
)

if TYPE_CHECKING:
    from fastapi import Request

    from shipgate.frontend.storage.sqlite import SqliteStorage


def overview_context(
    request: Request, storage: SqliteStorage, run_id: str | None
) -> dict[str, Any]:
    run, run_missing = resolve_overview_run(storage, run_id)
    latest = storage.list_runs(limit=1)
    baseline = load_baseline(request.app.state.primary_root)
    baseline_fps = fingerprints_from_report(baseline) if baseline else set()
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
    }
    if run is None:
        return context
    previous = storage.previous_completed_run(branch=run.branch, before_run_id=run.id)
    context["previous"] = previous
    context["deltas"] = severity_deltas(run.summary, previous.summary if previous else None)
    attach_baseline_context(context, run, baseline)
    code_findings = storage.list_findings(run.id, category=FindingCategory.CODE)
    context["hotspots"] = file_hotspots(code_findings)
    context["by_check"] = by_check_rows(run.summary)
    context["tool_failures"] = storage.list_findings(run.id, category=FindingCategory.TOOL)
    context["gate_status"] = gate_status(run)
    context["baseline_new_count"] = (
        sum(1 for f in code_findings if fingerprint_from_record(f) not in baseline_fps)
        if baseline_fps
        else None
    )
    return context


def attach_baseline_context(context: dict[str, Any], run: RunRecord, baseline) -> None:
    if run.summary and baseline and baseline.reports:
        baseline_sev: dict[str, int] = {}
        for check in baseline.reports:
            for finding in check.findings:
                baseline_sev[finding.severity] = baseline_sev.get(finding.severity, 0) + 1
        context["baseline_deltas"] = severity_deltas_vs_baseline(
            run.summary.by_severity, baseline_sev
        )


def gate_status(run: RunRecord) -> str | None:
    if run.summary is None:
        return None
    gate_checks = {k: v for k, v in run.summary.by_check_id.items() if k.startswith("gate.")}
    if not gate_checks:
        return "passed" if run.status.value == "succeeded" else "failed"
    if any(count > 0 for count in gate_checks.values()):
        return "failed"
    return "passed"


def resolve_overview_run(
    storage: SqliteStorage, run_id: str | None
) -> tuple[RunRecord | None, bool]:
    if run_id:
        run = storage.get_run(run_id)
        if run is None:
            return None, True
        return run, False
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
    if summary is None:
        return []
    return [
        {"check_id": check_id, "count": count}
        for check_id, count in sorted(
            summary.by_check_id.items(), key=lambda item: (-item[1], item[0])
        )
        if count > 0
    ]
