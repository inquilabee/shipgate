"""New-run page context and start-run actions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from fastapi.responses import RedirectResponse

from shipgate.config.loader import ProjectConfigLoader
from shipgate.errors import ConfigError
from shipgate.frontend.domain.requirements import acknowledge, is_acknowledged
from shipgate.frontend.services.orchestrator import OrchestratorError
from shipgate.frontend.services.worktree import WorktreeError
from shipgate.frontend.web.context.serialize import requirements_text

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi import Request

    from shipgate.frontend.services.orchestrator import RunOrchestrator
    from shipgate.frontend.services.worktree import WorktreeManager


def new_run_context(request: Request, error: str | None) -> dict[str, Any]:
    primary: Path = request.app.state.primary_root
    catalog = request.app.state.catalog
    worktrees: WorktreeManager = request.app.state.worktrees
    suite_checks: dict[str, list[str]] = {
        suite_id: list(suite.members) for suite_id, suite in catalog.suites.items()
    }
    selected_suite = default_suite(catalog, primary)
    return {
        "request": request,
        "branches": safe_branches(worktrees),
        "suites": sorted(catalog.suites),
        "suite_checks": suite_checks,
        "check_options": suite_checks.get(selected_suite, []),
        "default_suite": selected_suite,
        "needs_ack": not is_acknowledged(primary),
        "requirements_text": requirements_text(),
        "error": error,
        "csrf_token": request.app.state.csrf_token,
    }


def start_new_run(
    primary: Path,
    orchestrator: RunOrchestrator,
    branch: str,
    suite_id: str,
    acknowledge_requirements: str | None,
    *,
    check: str | None = None,
    changed_only: bool = False,
    since: str | None = None,
) -> RedirectResponse:
    if not is_acknowledged(primary):
        if not acknowledge_requirements:
            return RedirectResponse(
                url="/runs/new?error=Please+acknowledge+the+requirements+before+starting",
                status_code=303,
            )
        acknowledge(primary)
    try:
        run = orchestrator.start_run(
            branch,
            suite_id,
            check=check,
            changed_only=changed_only,
            since=since,
        )
    except OrchestratorError as exc:
        return RedirectResponse(url=f"/runs/new?error={query_escape(str(exc))}", status_code=303)
    return RedirectResponse(url=f"/?run_id={run.id}", status_code=303)


def safe_branches(worktrees: WorktreeManager) -> list[str]:
    try:
        return worktrees.list_branches()
    except WorktreeError:
        return []


def default_suite(catalog, primary: Path) -> str:
    project = None
    try:
        project = ProjectConfigLoader.load(project_root=primary)
    except ConfigError:
        project = None
    return (
        project.suite
        if project is not None and project.suite is not None and project.suite in catalog.suites
        else (
            "standard" if "standard" in catalog.suites else next(iter(sorted(catalog.suites)), "")
        )
    )


def query_escape(value: str) -> str:
    return quote(value, safe="")
