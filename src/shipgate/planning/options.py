"""Option precedence resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.planning.option_resolver import OptionResolver

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.options import NormalizedOptions
    from shipgate.domain.project import ProjectConfig


def resolve_option_sources(
    *,
    cli_options: NormalizedOptions,
    project: ProjectConfig,
    tool: ToolDefinition,
) -> tuple[NormalizedOptions, dict[str, str]]:
    return OptionResolver().resolve_sources(
        cli_options=cli_options,
        project=project,
        tool=tool,
    )
