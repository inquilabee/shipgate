"""Argv builder from resolved requests."""

from pathlib import Path

from shipgate.adapter.serialize import serialize_option
from shipgate.domain.catalog import CliOptionDefinition
from shipgate.domain.execution import ResolvedRequest


def build_argv(request: ResolvedRequest) -> tuple[str, ...]:
    tool = request.tool
    argv: list[str] = [tool.executable, *tool.subcommand]

    option_order = tool.option_order or tuple(tool.cli.keys())
    positional: list[str] = []

    for name in option_order:
        if name not in tool.cli:
            continue
        definition = tool.cli[name]
        value = _option_value(request, name)
        if value is None:
            continue
        value = _aggregate_paths(definition, value, request.project_root)
        if value is None:
            continue
        if definition.style == "positional":
            positional.extend(serialize_option(definition, value))
        else:
            argv.extend(serialize_option(definition, value))

    argv.extend(request.extra_args)
    argv.extend(positional)
    return tuple(argv)


def _option_value(request: ResolvedRequest, name: str) -> object | None:
    opts = request.options
    mapping = {
        "paths": tuple(str(p) for p in opts.paths) if opts.paths else None,
        "config": tuple(str(p) for p in opts.config) if opts.config else None,
        "exclude": opts.exclude or None,
        "output": str(opts.output) if opts.output else None,
        "format": opts.format,
        "verbose": opts.verbose,
        "quiet": opts.quiet,
        "fix": opts.fix,
        "check": opts.check,
        "rules": opts.rules or None,
        "threshold": opts.threshold,
    }
    return mapping.get(name)


def _aggregate_paths(
    definition: CliOptionDefinition,
    value: object,
    project_root: Path,
) -> object | None:
    if definition.aggregate != "root":
        return value
    if not isinstance(value, (list, tuple)):
        return value
    if not value:
        return None
    if len(value) == 1:
        return value[0]
    return project_root
