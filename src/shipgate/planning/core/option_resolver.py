"""Option precedence resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.paths import PROJECT_REPORTS_RAW_DIR

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig


class OptionResolver:
    """Resolve option precedence for one tool in one project context."""

    def __init__(
        self,
        project: ProjectConfig,
        project_root: Path,
        tool: ToolDefinition,
    ) -> None:
        self.project = project
        self.project_root = project_root
        self.tool = tool

    def resolve(
        self,
        cli_options: NormalizedOptions,
        *,
        mode: RunMode,
        check_id: str,
        target: Path,
    ) -> tuple[NormalizedOptions, dict[str, str]]:
        merged, sources = self._resolve_sources(cli_options)
        return self._apply_defaults(
            merged,
            mode=mode,
            check_id=check_id,
            target=target,
            sources=sources,
        )

    def _resolve_sources(
        self,
        cli_options: NormalizedOptions,
    ) -> tuple[NormalizedOptions, dict[str, str]]:
        sources: dict[str, str] = {}
        if paths := cli_options.paths:
            sources["paths"] = "cli"
        elif self.project.target != Path():
            paths = (self.project.target,)
            sources["paths"] = "project"

        verbose, quiet = self._resolve_verbose_quiet(cli_options, sources)
        fmt = self._resolve_format(cli_options, sources)
        output = cli_options.output
        if output is not None:
            sources["output"] = "cli"
        if config := cli_options.config:
            sources["config"] = "cli"

        threshold = self._resolve_threshold(cli_options, sources)
        extra = self._resolve_metric_options(cli_options, sources)

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
            threshold=threshold,
            python=cli_options.python,
            stdin=cli_options.stdin,
            exit_behavior=cli_options.exit_behavior,
            extra=extra,
        )
        return merged, sources

    def _resolve_format(
        self,
        cli_options: NormalizedOptions,
        sources: dict[str, str],
    ) -> str | None:
        fmt = cli_options.format
        if fmt is not None:
            sources["format"] = "cli"
            return fmt
        if os.environ.get("SHIPGATE_FORMAT"):
            sources["format"] = "environment"
            return os.environ["SHIPGATE_FORMAT"]
        if "format" in self.tool.cli:
            sources["format"] = "tool_default"
            return self.tool.cli["format"].default or "json"
        return fmt

    def _resolve_verbose_quiet(
        self,
        cli_options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[bool | None, bool | None]:
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
        return verbose, quiet

    def _resolve_threshold(
        self,
        cli_options: NormalizedOptions,
        sources: dict[str, str],
    ) -> str | None:
        threshold = cli_options.threshold
        if threshold is not None:
            sources["threshold"] = "cli"
            return threshold
        project_threshold = self.project.threshold_for_check(self.tool.id)
        if project_threshold is not None:
            sources["threshold"] = "project"
            return project_threshold
        if "threshold" in self.tool.cli:
            threshold = self.tool.cli["threshold"].default
            if threshold is not None:
                sources["threshold"] = "tool_default"
        return threshold

    def _resolve_metric_options(
        self,
        cli_options: NormalizedOptions,
        sources: dict[str, str],
    ) -> dict[str, object]:
        extra = dict(cli_options.extra)
        binding = self.project.binding_for_check(self.tool.id)
        if binding is None:
            return extra
        for name in (
            "average_mode",
            "average_threshold",
            "median_mode",
            "median_threshold",
            "minimum_mode",
            "minimum_threshold",
            "maximum_mode",
            "maximum_threshold",
            "p5_mode",
            "p5_threshold",
            "p10_mode",
            "p10_threshold",
            "p95_mode",
            "p95_threshold",
        ):
            if name in extra:
                continue
            value = getattr(binding, name)
            if value is not None:
                extra[name] = value
                sources[name] = "project"
        return extra

    def _apply_defaults(
        self,
        options: NormalizedOptions,
        *,
        mode: RunMode,
        check_id: str,
        target: Path,
        sources: dict[str, str],
    ) -> tuple[NormalizedOptions, dict[str, str]]:
        merged_sources = dict(sources)
        paths, merged_sources = self._default_paths(options, target, merged_sources)
        output, merged_sources = self._default_output(options, check_id, merged_sources)
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
            python=options.python,
            stdin=options.stdin,
            exit_behavior=options.exit_behavior,
            extra=dict(options.extra),
        )
        return resolved, merged_sources

    @staticmethod
    def _default_paths(
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
        sources: dict[str, str],
    ) -> tuple[Path, dict[str, str]]:
        output = options.output
        if output is None:
            output = self.project_root / PROJECT_REPORTS_RAW_DIR / f"{check_id}.json"
            sources["output"] = "shipgate_default"
        return output, sources

    @staticmethod
    def _default_format(
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[str, dict[str, str]]:
        fmt = options.format
        if fmt is None:
            fmt = "json"
            sources["format"] = "shipgate_default"
        return fmt, sources

    @staticmethod
    def _default_verbose(
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[bool, dict[str, str]]:
        verbose = options.verbose if options.verbose is not None else False
        if options.verbose is None:
            sources["verbose"] = "shipgate_default"
        return verbose, sources

    @staticmethod
    def _default_quiet(
        options: NormalizedOptions,
        sources: dict[str, str],
    ) -> tuple[bool, dict[str, str]]:
        quiet = options.quiet if options.quiet is not None else False
        if options.quiet is None:
            sources["quiet"] = "shipgate_default"
        return quiet, sources

    @staticmethod
    def _default_fix(
        options: NormalizedOptions,
        mode: RunMode,
        sources: dict[str, str],
    ) -> tuple[bool | None, dict[str, str]]:
        fix = options.fix
        if fix is None and mode == RunMode.APPLY:
            fix = True
            sources["fix"] = "shipgate_default"
        elif fix is None and mode == RunMode.CHECK:
            fix = False
            sources["fix"] = "shipgate_default"
        return fix, sources

    @staticmethod
    def _default_check(
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
