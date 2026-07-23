"""Compatibility facade for prepare_check — prefer CheckPlanner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.planning.check_planner import CheckPlanner, PreparedCheck

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog
    from shipgate.domain.run_command import RunCommand
    from shipgate.planning.workflow import PlannedCheck
    from shipgate.runtime.session.context import RunContext

__all__ = ["CheckPlanner", "PreparedCheck", "prepare_check"]


def prepare_check(
    *,
    planned: PlannedCheck,
    command: RunCommand,
    context: RunContext,
    catalog: Catalog,
) -> PreparedCheck:
    return CheckPlanner(
        project_root=context.project_root,
        project=context.project,
        catalog=catalog,
        scope_session=context.scope_session,
        environment=context.environment,
    ).prepare(planned, command)
