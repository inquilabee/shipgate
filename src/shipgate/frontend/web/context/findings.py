"""Findings page context builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from fastapi import HTTPException

from shipgate.baseline import load_baseline
from shipgate.frontend.domain.baseline import (
    fingerprint_from_record,
    fingerprints_from_report,
)
from shipgate.frontend.domain.finding_context import message_contexts, source_contexts
from shipgate.frontend.domain.models import FindingCategory, FindingRecord, RunRecord
from shipgate.paths import normalize_finding_path

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    from shipgate.frontend.storage.sqlite import SqliteStorage

FINDINGS_PAGE_SIZE = 50


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
    severity: str | None,
    check_id: str | None,
    file_filter: str | None,
    rule_id: str | None = None,
) -> dict[str, str | None]:
    return {
        "severity": severity or None,
        "check_id": check_id or None,
        "file": file_filter,
        "rule_id": rule_id or None,
    }


def filter_display(filters: dict[str, str | None], file_filter: str | None) -> dict[str, str]:
    return {
        "severity": filters["severity"] or "",
        "check_id": filters["check_id"] or "",
        "rule_id": filters.get("rule_id") or "",
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
        "rule_options": rule_options_for_run(run),
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
    rule_id: str | None = None,
) -> HTMLResponse:
    storage: SqliteStorage = request.app.state.storage
    run = storage.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    file_filter = normalize_finding_path(file) if file else None
    filters = finding_filters(severity, check_id, file_filter, rule_id)
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
    return (
        set()
        if not run.summary or not run.summary.by_check_id
        else {check_id for check_id, count in run.summary.by_check_id.items() if count > 0}
    )


def check_options_for_run(storage: SqliteStorage, run: RunRecord) -> list[str]:
    options = summary_check_ids(run)
    for finding in storage.list_findings(run.id):
        options.add(finding.check_id)
    return sorted(options)


def rule_options_for_run(run: RunRecord) -> list[str]:
    return [] if not run.summary or not run.summary.by_rule_id else sorted(run.summary.by_rule_id)
