"""Argv builder from resolved requests."""

from shipgate.adapter.serialize import serialize_option
from shipgate.domain.execution import ResolvedRequest


def build_argv(request: ResolvedRequest) -> tuple[str, ...]:
    tool = request.tool
    argv: list[str] = [tool.executable, *tool.subcommand]

    option_order = tool.option_order or tuple(tool.cli)

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
        argv.extend(serialize_option(definition, value))

    argv.extend(request.extra_args)
    return tuple(argv)


def option_value(request: ResolvedRequest, name: str) -> object | None:
    value = request.options.cli_value(name)
    return (
        value
        if value is not None
        else (request.tool.cli[name].default if name in request.tool.cli else None)
    )
