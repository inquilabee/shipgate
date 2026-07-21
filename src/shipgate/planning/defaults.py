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
    paths = options.paths or (target,)
    if not options.paths:
        merged_sources["paths"] = "shipgate_default"

    output = options.output
    if output is None:
        output = reports_root(project_root) / "raw" / f"{check_id}.json"
        merged_sources["output"] = "shipgate_default"

    fmt = options.format
    if fmt is None:
        fmt = "json"
        merged_sources["format"] = "shipgate_default"

    verbose = options.verbose if options.verbose is not None else False
    if options.verbose is None:
        merged_sources["verbose"] = "shipgate_default"

    quiet = options.quiet if options.quiet is not None else False
    if options.quiet is None:
        merged_sources["quiet"] = "shipgate_default"

    fix = options.fix
    if fix is None and mode == RunMode.APPLY:
        fix = True
        merged_sources["fix"] = "shipgate_default"

    check = options.check
    if check is None and mode == RunMode.CHECK:
        check = True
        merged_sources["check"] = "shipgate_default"

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
