"""Compatibility facade for prepare_run — prefer CheckResolver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.planning.check_resolver import CheckResolver, PreparedRun

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog
    from shipgate.domain.run_command import RunCommand
    from shipgate.planning.workflow import SelectedTool
    from shipgate.runtime.session.context import RunContext

__all__ = ["CheckResolver", "PreparedRun", "prepare_run"]


def prepare_run(
    *,
    selected: SelectedTool,
    command: RunCommand,
    context: RunContext,
    catalog: Catalog,
) -> PreparedRun:
    return CheckResolver(
        project_root=context.project_root,
        project=context.project,
        catalog=catalog,
        scope_session=context.scope_session,
        environment=context.environment,
    ).prepare(selected, command)
