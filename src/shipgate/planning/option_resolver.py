"""Option precedence resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.paths import reports_root

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig


class OptionResolver:
    def resolve(
        self,
        *,
        cli_options: NormalizedOptions,
        project: ProjectConfig,
        tool: ToolDefinition,
        mode: RunMode,
        check_id: str,
        project_root: Path,
        target: Path,
    ) -> tuple[NormalizedOptions, dict[str, str]]:
        merged, sources = self._resolve_sources(
            cli_options=cli_options,
            project=project,
            tool=tool,
        )
        return self._apply_defaults(
            merged,
            mode=mode,
            check_id=check_id,
            project_root=project_root,
            target=target,
            sources=sources,
        )

    def _resolve_sources(
        self,
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
        elif self._env_bool("SHIPGATE_VERBOSE"):
            verbose = True
            sources["verbose"] = "environment"

        quiet = cli_options.quiet
        if quiet is not None:
            sources["quiet"] = "cli"
        elif self._env_bool("SHIPGATE_QUIET"):
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

    def _apply_defaults(
        self,
        options: NormalizedOptions,
        *,
        mode: RunMode,
        check_id: str,
        project_root: Path,
        target: Path,
        sources: dict[str, str],
    ) -> tuple[NormalizedOptions, dict[str, str]]:
        merged_sources = dict(sources)
        paths, merged_sources = self._default_paths(options, target, merged_sources)
        output, merged_sources = self._default_output(
            options, check_id, project_root, merged_sources
        )
        fmt, merged_sources = self._default_format(options, merged_sources)
        verbose, merged_sources = self._default_verbose(options, merged_sources)
        quiet, merged_sources = self._default_quiet(options, merged_sources)
        fix, merged_sources = self._default_fix(options, mode, merged_sources)
        check, merged_sources = self._default_check(options, mode, merged_sources)

        resolved = NormalizedOptions(
            paths=paths,
            include=options.include,
            exclude=options.exclude,
            config=options.config,
            format=fmt,
            output=output,
            verbose=verbose,
            quiet=quiet,
            fix=fix,
            check=check,
            rules=options.rules,
            threshold=options.threshold,
            stdin=options.stdin,
            exit_behavior=options.exit_behavior,
            extra=dict(options.extra),
        )
        return resolved, merged_sources

    def _default_paths(
        self,
        options: NormalizedOptions,
        target: Path,
        sources: dict[str, str],
    ) -> tuple[tuple[Path, ...], dict[str, str]]:
        paths = options.paths or (target,)
        if not options.paths:
            sources["paths"] = "shipgate_default"
        return paths, sources

    def _default_output(
        self,
        options: NormalizedOptions,
        check_id: str,
        project_root: Path,
        sources: dict[str, str],
    ) -> tuple[Path, dict[str, str]]:
        output = options.output
        if output is None:
            output = reports_root(project_root) / "raw" / f"{check_id}.json"
            sources["output"] = "shipgate_default"
        return output, sources

    def _default_format(
        self,
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[str, dict[str, str]]:
        fmt = options.format
        if fmt is None:
            fmt = "json"
            sources["format"] = "shipgate_default"
        return fmt, sources

    def _default_verbose(
        self,
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[bool, dict[str, str]]:
        verbose = options.verbose if options.verbose is not None else False
        if options.verbose is None:
            sources["verbose"] = "shipgate_default"
        return verbose, sources

    def _default_quiet(
        self,
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[bool, dict[str, str]]:
        quiet = options.quiet if options.quiet is not None else False
        if options.quiet is None:
            sources["quiet"] = "shipgate_default"
        return quiet, sources

    def _default_fix(
        self,
        options: NormalizedOptions,
        mode: RunMode,
        sources: dict[str, str],
    ) -> tuple[bool | None, dict[str, str]]:
        fix = options.fix
        if fix is None and mode == RunMode.APPLY:
            fix = True
            sources["fix"] = "shipgate_default"
        return fix, sources

    def _default_check(
        self,
        options: NormalizedOptions,
        mode: RunMode,
        sources: dict[str, str],
    ) -> tuple[bool | None, dict[str, str]]:
        check = options.check
        if check is None and mode == RunMode.CHECK:
            check = True
            sources["check"] = "shipgate_default"
        return check, sources

    @staticmethod
    def _env_bool(name: str) -> bool:
        value = os.environ.get(name, "")
        return value.lower() in {"1", "true", "yes", "on"}
