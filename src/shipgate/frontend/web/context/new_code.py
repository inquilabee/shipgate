"""New/Fixed findings page context."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shipgate.baseline import load_baseline
from shipgate.frontend.domain.baseline import (
    fingerprint_from_record,
    fingerprints_from_report,
    fixed_finding_rows,
    fixed_fingerprints,
)
from shipgate.frontend.domain.models import FindingCategory

if TYPE_CHECKING:
    from fastapi import Request

    from shipgate.domain.reports import RunReport
    from shipgate.frontend.domain.models import FindingRecord, RunRecord
    from shipgate.frontend.storage.sqlite import SqliteStorage

FindingFingerprint = tuple[str, str, str, int | None, str]


def new_code_context(request: Request, storage: SqliteStorage, run: RunRecord) -> dict[str, Any]:
    baseline = load_baseline(request.app.state.primary_root)
    baseline_fps: set[FindingFingerprint] = (
        fingerprints_from_report(baseline) if baseline else set()
    )
    code_findings = storage.list_findings(run.id, category=FindingCategory.CODE)
    current_fps = {fingerprint_from_record(f) for f in code_findings}
    fixed_rows, fixed_count = baseline_fixed_summary(baseline, baseline_fps, current_fps)
    previous = storage.previous_completed_run(branch=run.branch, before_run_id=run.id)
    vs_previous_new, vs_previous_fixed_count = previous_run_deltas(
        storage, previous, code_findings, current_fps
    )
    return {
        "request": request,
        "run": run,
        "has_baseline": baseline_fps,
        "new_findings": baseline_new_findings(code_findings, baseline_fps),
        "fixed_rows": fixed_rows,
        "fixed_count": fixed_count,
        "previous": previous,
        "vs_previous_new": vs_previous_new,
        "vs_previous_fixed_count": vs_previous_fixed_count,
    }


def baseline_new_findings(
    code_findings: list[FindingRecord],
    baseline_fps: set[FindingFingerprint],
) -> list[FindingRecord]:
    return (
        [
            finding
            for finding in code_findings
            if fingerprint_from_record(finding) not in baseline_fps
        ]
        if baseline_fps
        else []
    )


def baseline_fixed_summary(
    baseline: RunReport | None,
    baseline_fps: set[FindingFingerprint],
    current_fps: set[FindingFingerprint],
) -> tuple[list[dict[str, str | int | None]], int]:
    if not baseline_fps or baseline is None:
        return [], 0
    fixed_fps = fixed_fingerprints(baseline_fps, current_fps)
    return fixed_finding_rows(baseline, fixed_fps, limit=50), len(fixed_fps)


def previous_run_deltas(
    storage: SqliteStorage,
    previous: RunRecord | None,
    code_findings: list[FindingRecord],
    current_fps: set[FindingFingerprint],
) -> tuple[list[FindingRecord], int]:
    if previous is None:
        return [], 0
    prev_findings = storage.list_findings(previous.id, category=FindingCategory.CODE)
    prev_fps = {fingerprint_from_record(finding) for finding in prev_findings}
    vs_previous_new = [
        finding for finding in code_findings if fingerprint_from_record(finding) not in prev_fps
    ]
    return vs_previous_new, len(fixed_fingerprints(prev_fps, current_fps))
