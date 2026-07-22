"""Option precedence resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.options import NormalizedOptions

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig


def resolve_option_sources(
    *,
    cli_options: NormalizedOptions,
    project: ProjectConfig,
    tool: ToolDefinition,
) -> tuple[NormalizedOptions, dict[str, str]]:
    sources: dict[str, str] = {}
    paths = cli_options.paths
    if paths:
        sources["paths"] = "cli"
    elif project.target != Path():
        paths = (project.target,)
        sources["paths"] = "project"

    verbose = cli_options.verbose
    if verbose is not None:
        sources["verbose"] = "cli"
    elif _env_bool("SHIPGATE_VERBOSE"):
        verbose = True
        sources["verbose"] = "environment"

    quiet = cli_options.quiet
    if quiet is not None:
        sources["quiet"] = "cli"
    elif _env_bool("SHIPGATE_QUIET"):
        quiet = True
        sources["quiet"] = "environment"

    fmt = cli_options.format
    if fmt is not None:
        sources["format"] = "cli"
    elif os.environ.get("SHIPGATE_FORMAT"):
        fmt = os.environ["SHIPGATE_FORMAT"]
        sources["format"] = "environment"
    elif "format" in tool.cli:
        fmt = tool.cli["format"].default or "json"
        sources["format"] = "tool_default"

    output = cli_options.output
    if output is not None:
        sources["output"] = "cli"

    config = cli_options.config
    if config:
        sources["config"] = "cli"

    merged = NormalizedOptions(
        paths=paths or cli_options.paths,
        include=cli_options.include,
        exclude=cli_options.exclude,
        config=config or cli_options.config,
        format=fmt,
        output=output,
        verbose=verbose,
        quiet=quiet,
        fix=cli_options.fix,
        check=cli_options.check,
        rules=cli_options.rules,
        threshold=cli_options.threshold,
        stdin=cli_options.stdin,
        exit_behavior=cli_options.exit_behavior,
        extra=dict(cli_options.extra),
    )
    return merged, sources


def _env_bool(name: str) -> bool:
    value = os.environ.get(name, "")
    return value.lower() in {"1", "true", "yes", "on"}
