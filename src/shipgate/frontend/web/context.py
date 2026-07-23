"""Template context builders for the report UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from shipgate.baseline import load_baseline
from shipgate.config.loader import ProjectConfigLoader
from shipgate.frontend.domain.baseline import (
    fingerprint_from_record,
    fingerprints_from_report,
    severity_deltas_vs_baseline,
)
from shipgate.frontend.domain.finding_context import message_contexts, source_contexts
from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunRecord,
    RunSummaryRecord,
)
from shipgate.frontend.domain.requirements import acknowledge, is_acknowledged
from shipgate.frontend.services.orchestrator import OrchestratorError, RunOrchestrator
from shipgate.frontend.services.worktree import WorktreeError, WorktreeManager
from shipgate.paths import normalize_finding_path

if TYPE_CHECKING:
    from shipgate.frontend.storage.sqlite import SqliteStorage

FINDINGS_PAGE_SIZE = 50
REQUIREMENTS_TEXT = (
    "This run uses a separate git worktree under `.shipgate/worktrees/` so your current "
    "checkout is not switched. Quality tools run from shipgate's managed environment under "
    "`.shipgate/tools/`. Disk space is used under `.shipgate/` for worktrees, tools, and "
    "the local SQLite database."
)


def finding_to_api(finding: FindingRecord) -> dict[str, object]:
    return {
        "id": finding.id,
        "check_id": finding.check_id,
        "tool_id": finding.tool_id,
        "rule_id": finding.rule_id,
        "severity": finding.severity,
        "message": finding.message,
        "file": finding.file,
        "line": finding.line,
        "column": finding.column,
        "category": finding.category.value,
    }


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


def attach_baseline_context(
    context: dict[str, Any],
    run: RunRecord,
    baseline,
) -> None:
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


def new_run_context(request: Request, error: str | None) -> dict[str, Any]:
    primary: Path = request.app.state.primary_root
    catalog = request.app.state.catalog
    worktrees: WorktreeManager = request.app.state.worktrees
    return {
        "request": request,
        "branches": safe_branches(worktrees),
        "suites": sorted(catalog.suites.keys()),
        "default_suite": default_suite(catalog, primary),
        "needs_ack": not is_acknowledged(primary),
        "requirements_text": REQUIREMENTS_TEXT,
        "error": error,
    }


def start_new_run(
    primary: Path,
    orchestrator: RunOrchestrator,
    branch: str,
    suite_id: str,
    acknowledge_requirements: str | None,
) -> RedirectResponse:
    if not is_acknowledged(primary):
        if not acknowledge_requirements:
            return RedirectResponse(
                url="/runs/new?error=Please+acknowledge+the+requirements+before+starting",
                status_code=303,
            )
        acknowledge(primary)
    try:
        run = orchestrator.start_run(branch, suite_id)
    except OrchestratorError as exc:
        return RedirectResponse(url=f"/runs/new?error={query_escape(str(exc))}", status_code=303)
    return RedirectResponse(url=f"/?run_id={run.id}", status_code=303)


@dataclass
class FindingsPage:
    total: int
    page: int
    total_pages: int
    offset: int
    page_size: int
    code_findings: list[FindingRecord]
    tool_failures: list[FindingRecord]
    showing_from: int
    showing_to: int


def finding_filters(
    severity: str | None, check_id: str | None, file_filter: str | None
) -> dict[str, str | None]:
    return {
        "severity": severity or None,
        "check_id": check_id or None,
        "file": file_filter,
    }


def filter_display(filters: dict[str, str | None], file_filter: str | None) -> dict[str, str]:
    return {
        "severity": filters["severity"] or "",
        "check_id": filters["check_id"] or "",
        "file": file_filter or "",
    }


def load_findings_page(
    storage: SqliteStorage,
    run_id: str,
    filters: dict[str, str | None],
    page: int,
) -> FindingsPage:
    page_size = FINDINGS_PAGE_SIZE
    total = storage.count_findings(run_id, category=FindingCategory.CODE, **filters)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    page = min(page, total_pages)
    offset = (page - 1) * page_size
    code_findings = storage.list_findings(
        run_id,
        category=FindingCategory.CODE,
        limit=page_size,
        offset=offset,
        **filters,
    )
    tool_failures = storage.list_findings(
        run_id,
        category=FindingCategory.TOOL,
        check_id=filters["check_id"],
        severity=filters["severity"],
    )
    return FindingsPage(
        total=total,
        page=page,
        total_pages=total_pages,
        offset=offset,
        page_size=page_size,
        code_findings=code_findings,
        tool_failures=tool_failures,
        showing_from=offset + 1 if total else 0,
        showing_to=offset + len(code_findings),
    )


def findings_nav_urls(
    run_id: str, query: dict[str, str], page: FindingsPage
) -> tuple[str | None, str | None]:
    prev_url = findings_page_url(run_id, query, page.page - 1) if page.page > 1 else None
    next_url = (
        findings_page_url(run_id, query, page.page + 1) if page.page < page.total_pages else None
    )
    return prev_url, next_url


def active_query(filters: dict[str, str | None], file_filter: str | None) -> dict[str, str]:
    return {k: v for k, v in filter_display(filters, file_filter).items() if v}


def page_message_contexts(page: FindingsPage, source_ctx: dict[str, Any]) -> dict[str, Any]:
    extra = [finding for finding in page.code_findings if finding.id not in source_ctx]
    return message_contexts(page.tool_failures + extra)


def findings_context(
    request: Request,
    run: RunRecord,
    storage: SqliteStorage,
    filters: dict[str, str | None],
    file_filter: str | None,
    page: FindingsPage,
) -> dict[str, Any]:
    query = active_query(filters, file_filter)
    project_root = Path(run.worktree_path) if run.worktree_path else request.app.state.primary_root
    source_ctx = source_contexts(project_root, page.code_findings)
    message_ctx = page_message_contexts(page, source_ctx)
    prev_url, next_url = findings_nav_urls(run.id, query, page)
    baseline = load_baseline(request.app.state.primary_root)
    baseline_fps = fingerprints_from_report(baseline) if baseline else set()
    new_finding_ids = (
        {f.id for f in page.code_findings if fingerprint_from_record(f) not in baseline_fps}
        if baseline_fps
        else set()
    )
    return {
        "request": request,
        "run": run,
        "findings": page.code_findings,
        "source_contexts": source_ctx,
        "message_contexts": message_ctx,
        "tool_failures": page.tool_failures,
        "check_options": check_options_for_run(storage, run),
        "new_finding_ids": new_finding_ids,
        **filter_display(filters, file_filter),
        "page": page.page,
        "page_size": page.page_size,
        "total": page.total,
        "total_pages": page.total_pages,
        "showing_from": page.showing_from,
        "showing_to": page.showing_to,
        "prev_page_url": prev_url,
        "next_page_url": next_url,
    }


def findings_response(
    request: Request,
    run_id: str,
    severity: str | None,
    check_id: str | None,
    file: str | None,
    page: int,
) -> HTMLResponse:
    storage: SqliteStorage = request.app.state.storage
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    file_filter = normalize_finding_path(file) if file else None
    filters = finding_filters(severity, check_id, file_filter)
    page_data = load_findings_page(storage, run_id, filters, page)
    context = findings_context(request, run, storage, filters, file_filter, page_data)
    return request.app.state.templates.TemplateResponse(request, "findings.html", context)


def findings_page_url(run_id: str, query: dict[str, str], page: int) -> str:
    params = dict(query)
    if page > 1:
        params["page"] = str(page)
    qs = urlencode(params)
    base = f"/runs/{run_id}/findings"
    return f"{base}?{qs}" if qs else base


def summary_check_ids(run: RunRecord) -> set[str]:
    if not run.summary or not run.summary.by_check_id:
        return set()
    return {check_id for check_id, count in run.summary.by_check_id.items() if count > 0}


def check_options_for_run(storage: SqliteStorage, run: RunRecord) -> list[str]:
    options = summary_check_ids(run)
    for finding in storage.list_findings(run.id):
        options.add(finding.check_id)
    return sorted(options)


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


def safe_branches(worktrees: WorktreeManager) -> list[str]:
    try:
        return worktrees.list_branches()
    except WorktreeError:
        return []


def default_suite(catalog, primary: Path) -> str:
    project = None
    try:
        project = ProjectConfigLoader.load(project_root=primary)
    except Exception:
        project = None
    if project is not None and project.suite is not None and project.suite in catalog.suites:
        return project.suite
    if "standard" in catalog.suites:
        return "standard"
    return next(iter(sorted(catalog.suites.keys())), "")


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


def query_escape(value: str) -> str:
    return quote(value, safe="")
