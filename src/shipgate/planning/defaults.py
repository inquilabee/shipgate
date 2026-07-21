"""Default option resolution."""

from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.paths import reports_root


def apply_defaults(
    options: NormalizedOptions,
    *,
    mode: RunMode,
    check_id: str,
    project_root: Path,
    target: Path,
    sources: dict[str, str],
) -> tuple[NormalizedOptions, dict[str, str]]:
    merged_sources = dict(sources)
    paths, merged_sources = _default_paths(options, target, merged_sources)
    output, merged_sources = _default_output(options, check_id, project_root, merged_sources)
    fmt, merged_sources = _default_format(options, merged_sources)
    verbose, merged_sources = _default_verbose(options, merged_sources)
    quiet, merged_sources = _default_quiet(options, merged_sources)
    fix, merged_sources = _default_fix(options, mode, merged_sources)
    check, merged_sources = _default_check(options, mode, merged_sources)

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
    options: NormalizedOptions,
    target: Path,
    sources: dict[str, str],
) -> tuple[tuple[Path, ...], dict[str, str]]:
    paths = options.paths or (target,)
    if not options.paths:
        sources["paths"] = "shipgate_default"
    return paths, sources


def _default_output(
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
    options: NormalizedOptions,
    sources: dict[str, str],
) -> tuple[str, dict[str, str]]:
    fmt = options.format
    if fmt is None:
        fmt = "json"
        sources["format"] = "shipgate_default"
    return fmt, sources


def _default_verbose(
    options: NormalizedOptions,
    sources: dict[str, str],
) -> tuple[bool, dict[str, str]]:
    verbose = options.verbose if options.verbose is not None else False
    if options.verbose is None:
        sources["verbose"] = "shipgate_default"
    return verbose, sources


def _default_quiet(
    options: NormalizedOptions,
    sources: dict[str, str],
) -> tuple[bool, dict[str, str]]:
    quiet = options.quiet if options.quiet is not None else False
    if options.quiet is None:
        sources["quiet"] = "shipgate_default"
    return quiet, sources


def _default_fix(
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
    options: NormalizedOptions,
    mode: RunMode,
    sources: dict[str, str],
) -> tuple[bool | None, dict[str, str]]:
    check = options.check
    if check is None and mode == RunMode.CHECK:
        check = True
        sources["check"] = "shipgate_default"
    return check, sources
