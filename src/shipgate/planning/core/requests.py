"""Execution request building and resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.execution import (
    ExecutionEnvironment,
    ExecutionRequest,
    ResolvedRequest,
)
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.project import ProjectConfig
from shipgate.errors import PlanningError
from shipgate.planning.core.option_resolver import OptionResolver

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import ToolDefinition


def build_execution_request(
    *,
    runnable: str,
    mode: RunMode,
    project_root: Path,
    options: NormalizedOptions | None = None,
    extra_args: tuple[str, ...] = (),
) -> ExecutionRequest:
    return ExecutionRequest(
        runnable=runnable,
        mode=mode,
        options=options or NormalizedOptions(),
        extra_args=extra_args,
        project_root=project_root,
    )


def resolve_request(
    request: ExecutionRequest,
    tool: ToolDefinition,
    environment: ExecutionEnvironment,
    *,
    target: Path,
    project: ProjectConfig | None = None,
    option_sources: dict[str, str] | None = None,
) -> ResolvedRequest:
    if request.mode not in tool.modes:
        raise PlanningError(
            f"tool {tool.id!r} does not support mode {request.mode.value!r}",
            hint=f"supported modes: {', '.join(m.value for m in tool.modes)}",
        )
    if request.options.verbose and request.options.quiet:
        raise PlanningError("cannot set both verbose and quiet")

    sources = dict(option_sources or {})
    project_config = project or ProjectConfig()
    options, precedence_sources = OptionResolver(
        project_config,
        request.project_root,
        tool,
    ).resolve(
        request.options,
        mode=request.mode,
        check_id=tool.id,
        target=target,
    )
    sources.update(precedence_sources)

    if request.mode == RunMode.CHECK and options.fix:
        raise PlanningError("fix is not allowed in check mode")

    output_path = options.output or (
        request.project_root / ".shipgate" / "reports" / "raw" / f"{tool.id}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return ResolvedRequest(
        runnable=request.runnable,
        tool=tool,
        mode=request.mode,
        options=options,
        option_sources=sources,
        extra_args=request.extra_args,
        project_root=request.project_root,
        output_path=output_path,
        environment=environment,
    )
