"""FastAPI report UI for local suite runs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from shipgate import __version__ as shipgate_version
from shipgate.catalog.loader import CatalogLoader
from shipgate.frontend.domain.models import FindingCategory
from shipgate.frontend.services.backfill import backfill_from_report_store
from shipgate.frontend.services.ingest import repair_misclassified_tool_findings
from shipgate.frontend.services.orchestrator import RunOrchestrator
from shipgate.frontend.services.report_access import store_for_run
from shipgate.frontend.services.tool_versions import tool_docs_rows
from shipgate.frontend.services.worktree import WorktreeManager
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.frontend.web.context import (
    finding_filters,
    finding_to_api,
    findings_response,
    new_run_context,
    overview_context,
    run_to_api,
    start_new_run,
)
from shipgate.frontend.web.context.overview import overview_payload, trends_payload
from shipgate.frontend.web.context.run_actions import query_escape
from shipgate.frontend.web.security import (
    UI_AUTH_HEADER,
    UI_SESSION_COOKIE,
    UI_UNLOCK_PATH,
    UiSessionStore,
    is_public_ui_path,
    new_csrf_token,
    ui_token_from_env,
    ui_token_matches,
    validate_csrf_token,
    validate_run_submit_tokens,
)
from shipgate.paths import (
    PROJECT_SERVER_DIR,
    SERVER_DB_FILENAME,
    contained_child,
    normalize_finding_path,
)

FRONTEND_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = FRONTEND_ROOT / "templates"
STATIC_DIR = FRONTEND_ROOT / "static"
RUN_NOT_FOUND = "run not found"
GITHUB_REPO_URL = "https://github.com/inquilabee/shipgate"
NEW_RUN_PATH = "/runs/new"


def contained_file(root: Path, rel_path: str) -> Path:
    """Resolve a UI file under ``root``. Follow the leaf, then refuse symlink escape."""
    try:
        candidate = contained_child(root, rel_path)
    except ValueError as exc:
        raise ValueError("path escapes root") from exc
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("path escapes root")
    if not resolved.is_file():
        raise FileNotFoundError(rel_path)
    return resolved


def create_app(primary_root: Path, *, require_ui_token: bool = False) -> FastAPI:
    primary = Path(primary_root).resolve()
    storage = SqliteStorage(primary / PROJECT_SERVER_DIR / SERVER_DB_FILENAME)
    backfill_from_report_store(primary, storage)
    repair_misclassified_tool_findings(storage)
    catalog = CatalogLoader.load()
    from shipgate.app import ShipGateApp

    app_instance = ShipGateApp(catalog=catalog)
    orchestrator = RunOrchestrator(primary, storage, app_instance)
    worktrees = WorktreeManager(primary)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    cast("dict[str, object]", templates.env.globals).update(
        {
            "github_repo_url": GITHUB_REPO_URL,
            "shipgate_version": shipgate_version,
            "ui_test_mode": os.environ.get("SHIPGATE_UI_TEST") == "1",
        },
    )

    fastapi_app = FastAPI(title="ShipGate Reports")
    fastapi_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    fastapi_app.state.primary_root = primary
    fastapi_app.state.storage = storage
    fastapi_app.state.catalog = catalog
    fastapi_app.state.orchestrator = orchestrator
    fastapi_app.state.worktrees = worktrees
    fastapi_app.state.templates = templates
    fastapi_app.state.csrf_token = new_csrf_token()
    fastapi_app.state.require_ui_token = require_ui_token
    fastapi_app.state.ui_sessions = UiSessionStore()
    register_ui_access_middleware(fastapi_app)
    register_routes(fastapi_app)
    return fastapi_app


def denied_ui_response(request: Request) -> RedirectResponse | JSONResponse:
    return (
        RedirectResponse(url=UI_UNLOCK_PATH, status_code=303)
        if request.method == "GET" and "text/html" in request.headers.get("accept", "*/*")
        else JSONResponse({"detail": "UI token required"}, status_code=403)
    )


def register_ui_access_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def require_ui_access(request: Request, call_next):
        return (
            await call_next(request)
            if (not request.app.state.require_ui_token or is_public_ui_path(request.url.path))
            or ui_access_allowed(request)
            else denied_ui_response(request)
        )


def register_routes(app: FastAPI) -> None:
    register_health_routes(app)
    register_overview_routes(app)
    register_ui_token_routes(app)
    register_run_routes(app)
    register_run_log_routes(app)
    register_tool_routes(app)
    register_api_routes(app)


def register_health_routes(app: FastAPI) -> None:
    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}


def register_overview_routes(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request, run_id: str | None = None) -> HTMLResponse:
        storage: SqliteStorage = request.app.state.storage
        templates: Jinja2Templates = request.app.state.templates
        return templates.TemplateResponse(
            request, "overview.html", overview_context(request, storage, run_id)
        )


def register_run_routes(app: FastAPI) -> None:
    register_run_list_routes(app)
    register_new_run_routes(app)
    register_cancel_routes(app)
    register_findings_routes(app)
    register_run_detail_routes(app)


def register_run_list_routes(app: FastAPI) -> None:
    @app.get("/runs", response_class=HTMLResponse)
    def runs_list(request: Request) -> HTMLResponse:
        storage: SqliteStorage = request.app.state.storage
        templates: Jinja2Templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "runs.html",
            {"request": request, "runs": storage.list_runs(limit=50)},
        )


def ui_access_allowed(request: Request) -> bool:
    if not request.app.state.require_ui_token:
        return True
    expected = ui_token_from_env()
    header = request.headers.get(UI_AUTH_HEADER)
    if ui_token_matches(header, expected):
        return True
    sessions: UiSessionStore = request.app.state.ui_sessions
    return sessions.is_unlocked(request.cookies.get(UI_SESSION_COOKIE))


def require_run_submit_tokens(request: Request, *, csrf_token: str | None) -> None:
    sessions: UiSessionStore = request.app.state.ui_sessions
    cookie = request.cookies.get(UI_SESSION_COOKIE)
    if sessions.is_unlocked(cookie):
        try:
            validate_csrf_token(
                csrf_expected=request.app.state.csrf_token,
                csrf_submitted=csrf_token,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return
    try:
        validate_run_submit_tokens(
            csrf_expected=request.app.state.csrf_token,
            csrf_submitted=csrf_token,
            ui_token_expected=ui_token_from_env(),
            ui_token_submitted=request.headers.get(UI_AUTH_HEADER),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def require_csrf_token(request: Request, csrf_token: str | None) -> None:
    try:
        validate_csrf_token(
            csrf_expected=request.app.state.csrf_token,
            csrf_submitted=csrf_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def set_ui_session_cookie(response: RedirectResponse, session_id: str) -> RedirectResponse:
    response.set_cookie(
        UI_SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="strict",
        path="/",
    )
    return response


def register_ui_token_routes(app: FastAPI) -> None:
    @app.get(UI_UNLOCK_PATH, response_class=HTMLResponse)
    def ui_token_form(request: Request, error: str | None = None) -> HTMLResponse:
        if not request.app.state.require_ui_token:
            raise HTTPException(status_code=404, detail="ui token is not required")
        return request.app.state.templates.TemplateResponse(
            request,
            "ui_token.html",
            {
                "request": request,
                "error": error,
                "csrf_token": request.app.state.csrf_token,
            },
        )

    @app.post(UI_UNLOCK_PATH)
    def ui_token_submit(
        request: Request,
        csrf_token: str | None = Form(None),
        token: str | None = Form(None),
    ) -> RedirectResponse:
        if not request.app.state.require_ui_token:
            raise HTTPException(status_code=404, detail="ui token is not required")
        require_csrf_token(request, csrf_token)
        expected = ui_token_from_env()
        if expected is None or not ui_token_matches(token, expected):
            return RedirectResponse(
                url=f"{UI_UNLOCK_PATH}?error={query_escape('invalid UI token')}",
                status_code=303,
            )
        sessions: UiSessionStore = request.app.state.ui_sessions
        return set_ui_session_cookie(
            RedirectResponse(url=NEW_RUN_PATH, status_code=303),
            sessions.issue(),
        )


def register_new_run_routes(app: FastAPI) -> None:
    @app.get(NEW_RUN_PATH, response_class=HTMLResponse)
    def new_run_form(request: Request, error: str | None = None) -> HTMLResponse:
        return request.app.state.templates.TemplateResponse(
            request,
            "new_run.html",
            new_run_context(request, error),
        )

    @app.post(NEW_RUN_PATH)
    def new_run_submit(
        request: Request,
        branch: str = Form(...),
        suite_id: str = Form(...),
        check: str | None = Form(None),
        changed_only: str | None = Form(None),
        since: str | None = Form(None),
        csrf_token: str | None = Form(None),
        acknowledge_requirements: str | None = Form(None),
    ) -> RedirectResponse:
        require_run_submit_tokens(request, csrf_token=csrf_token)
        return start_new_run(
            request.app.state.primary_root,
            request.app.state.orchestrator,
            branch,
            suite_id,
            acknowledge_requirements,
            check=check or None,
            changed_only=changed_only not in (None, ""),
            since=since or None,
        )


def register_cancel_routes(app: FastAPI) -> None:
    @app.post("/runs/{run_id}/cancel")
    def cancel_run(
        request: Request,
        run_id: str,
        csrf_token: str | None = Form(None),
    ) -> RedirectResponse:
        require_run_submit_tokens(request, csrf_token=csrf_token)
        orchestrator: RunOrchestrator = request.app.state.orchestrator
        if not orchestrator.request_cancel(run_id):
            raise HTTPException(status_code=404, detail="run not cancellable")
        return RedirectResponse(url=f"/?run_id={run_id}", status_code=303)


def register_findings_routes(app: FastAPI) -> None:
    @app.get("/runs/{run_id}/findings", response_class=HTMLResponse)
    def findings_page(
        request: Request,
        run_id: str,
        severity: str | None = Query(None),
        check_id: str | None = Query(None),
        rule_id: str | None = Query(None),
        file: str | None = Query(None),
        page: int = Query(1, ge=1),
    ) -> HTMLResponse:
        return findings_response(request, run_id, severity, check_id, file, page, rule_id)


def register_run_detail_routes(app: FastAPI) -> None:
    @app.get("/runs/{run_id}/new-code", response_class=HTMLResponse)
    def new_code_page(request: Request, run_id: str) -> HTMLResponse:
        from shipgate.frontend.web.context.new_code import new_code_context

        storage: SqliteStorage = request.app.state.storage
        run = storage.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND)
        return request.app.state.templates.TemplateResponse(
            request,
            "new_code.html",
            new_code_context(request, storage, run),
        )

    @app.get("/partials/runs/{run_id}/progress", response_class=HTMLResponse)
    def run_progress(request: Request, run_id: str) -> HTMLResponse:
        run = request.app.state.storage.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND)
        return request.app.state.templates.TemplateResponse(
            request,
            "partials/run_progress.html",
            {
                "request": request,
                "run": run,
                "csrf_token": request.app.state.csrf_token,
            },
        )


def register_run_log_routes(app: FastAPI) -> None:
    @app.get("/runs/{run_id}/checks/{check_id}/log")
    def check_log(
        request: Request, run_id: str, check_id: str, stream: str = "stdout"
    ) -> PlainTextResponse:
        primary: Path = request.app.state.primary_root
        storage: SqliteStorage = request.app.state.storage
        run = storage.get_run(run_id)
        store = store_for_run(primary, run)
        try:
            report = store.load(run_id)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND) from exc
        check_report = next((c for c in report.reports if c.check_id == check_id), None)
        if check_report is None:
            raise HTTPException(status_code=404, detail="check not found")
        rel_path = check_report.stderr_path if stream == "stderr" else check_report.stdout_path
        if not rel_path:
            raise HTTPException(status_code=404, detail="log not found")
        root = Path(run.worktree_path) if run and run.worktree_path else primary
        try:
            path = contained_file(root, rel_path)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="log file missing") from exc
        return PlainTextResponse(path.read_text(encoding="utf-8", errors="replace"))


def register_tool_routes(app: FastAPI) -> None:
    @app.get("/tools", response_class=HTMLResponse)
    def tool_docs(request: Request) -> HTMLResponse:
        catalog = request.app.state.catalog
        primary: Path = request.app.state.primary_root
        return request.app.state.templates.TemplateResponse(
            request,
            "tools.html",
            {"request": request, "tools": tool_docs_rows(catalog, primary)},
        )


def register_api_routes(app: FastAPI) -> None:
    register_api_run_list_routes(app)
    register_api_run_detail_routes(app)
    register_api_findings_routes(app)


def register_api_run_list_routes(app: FastAPI) -> None:
    @app.get("/api/runs")
    def api_runs(request: Request) -> dict[str, list[dict]]:
        storage: SqliteStorage = request.app.state.storage
        return {"runs": [run_to_api(run) for run in storage.list_runs(limit=50)]}

    @app.get("/api/runs/trends")
    def api_trends(
        request: Request,
        branch: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, list[dict]]:
        storage: SqliteStorage = request.app.state.storage
        return {"runs": trends_payload(storage, branch=branch, limit=limit)}


def register_api_run_detail_routes(app: FastAPI) -> None:
    @app.get("/api/runs/{run_id}")
    def api_run(request: Request, run_id: str) -> dict:
        primary: Path = request.app.state.primary_root
        storage: SqliteStorage = request.app.state.storage
        run = storage.get_run(run_id)
        store = store_for_run(primary, run)
        try:
            report = store.load(run_id)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND) from exc
        return report.to_dict()

    @app.get("/api/runs/{run_id}/overview")
    def api_run_overview(request: Request, run_id: str) -> dict:
        storage: SqliteStorage = request.app.state.storage
        payload = overview_payload(storage, request.app.state.primary_root, run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND)
        return payload

    @app.get("/api/runs/{run_id}/summary")
    def api_run_summary(request: Request, run_id: str) -> dict:
        storage: SqliteStorage = request.app.state.storage
        run = storage.get_run(run_id)
        if run is None or run.summary is None:
            raise HTTPException(status_code=404, detail="summary not found")
        return run.summary.to_dict()


def register_api_findings_routes(app: FastAPI) -> None:
    @app.get("/api/runs/{run_id}/findings")
    def api_run_findings(
        request: Request,
        run_id: str,
        severity: str | None = Query(None),
        check_id: str | None = Query(None),
        rule_id: str | None = Query(None),
        file: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=200),
    ) -> dict:
        storage: SqliteStorage = request.app.state.storage
        if storage.get_run(run_id) is None:
            raise HTTPException(status_code=404, detail=RUN_NOT_FOUND)
        file_filter = normalize_finding_path(file) if file else None
        filters = finding_filters(severity, check_id, file_filter, rule_id)
        total = storage.count_findings(run_id, category=FindingCategory.CODE, **filters)
        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
        page = min(page, total_pages)
        offset = (page - 1) * page_size
        findings = storage.list_findings(
            run_id,
            category=FindingCategory.CODE,
            limit=page_size,
            offset=offset,
            **filters,
        )
        return {
            "run_id": run_id,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "findings": [finding_to_api(f) for f in findings],
        }
