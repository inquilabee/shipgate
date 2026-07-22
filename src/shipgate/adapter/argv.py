"""Argv builder from resolved requests."""

from shipgate.adapter.serialize import serialize_option
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
        value = option_value(request, name)
        if value is None:
            continue
        value = definition.aggregate_value(value, request.project_root)
        if value is None:
            continue
        if definition.style == "positional":
            positional.extend(serialize_option(definition, value))
        else:
            argv.extend(serialize_option(definition, value))

    argv.extend(request.extra_args)
    argv.extend(positional)
    return tuple(argv)


def option_value(request: ResolvedRequest, name: str) -> object | None:
    return request.options.cli_value(name)
