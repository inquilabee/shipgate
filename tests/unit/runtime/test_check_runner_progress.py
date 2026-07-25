from pathlib import Path
from unittest.mock import MagicMock

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.domain.reports import CheckReport
from shipgate.domain.run_command import RunCommand
from shipgate.planning.utils.incremental import RunScopeSession
from shipgate.planning.workflow import SelectedTool
from shipgate.runtime.environment import resolve_environment
from shipgate.runtime.session.check_runner import CheckRunner
from shipgate.runtime.session.context import RunContext, RunProgress


def make_context(tmp_path: Path, *, parallel: bool, tool_ids: tuple[str, ...]) -> RunContext:
    tools = tuple(SelectedTool(tool_id=tool_id, mode=RunMode.CHECK) for tool_id in tool_ids)
    return RunContext(
        project=ProjectConfig(env="system", target=Path()),
        project_root=tmp_path,
        suite_id="test",
        selected_tools=tools,
        environment=resolve_environment(tmp_path, "system"),
        parallel=parallel,
        fail_fast=False,
        scope_session=RunScopeSession(project_root=tmp_path, changed_only=False, since=None),
    )


def passed_report(tool_id: str) -> CheckReport:
    return CheckReport(check_id=tool_id, tool_id=tool_id, status="passed", exit_code=0)


def collect_progress(
    tmp_path: Path,
    monkeypatch,
    *,
    parallel: bool,
) -> tuple[list[CheckReport], list[RunProgress]]:
    catalog = CatalogLoader.load()
    runner = CheckRunner(catalog=catalog, executor=MagicMock(), executor_is_default=False)
    tool_ids = ("a.tool", "b.tool", "c.tool")
    context = make_context(tmp_path, parallel=parallel, tool_ids=tool_ids)
    events: list[RunProgress] = []

    def fake_run_selected_tool(self, *, selected, command, context, run_id):
        del self, command, context, run_id
        return passed_report(selected.tool_id)

    monkeypatch.setattr(CheckRunner, "run_selected_tool", fake_run_selected_tool)
    reports = runner.run_all_checks(
        command=RunCommand(project_root=tmp_path),
        context=context,
        run_id="run-1",
        on_progress=events.append,
    )
    return reports, events


def test_run_all_checks_emits_progress_sequential(tmp_path: Path, monkeypatch):
    reports, events = collect_progress(tmp_path, monkeypatch, parallel=False)
    assert [report.tool_id for report in reports] == ["a.tool", "b.tool", "c.tool"]
    assert events[0] == RunProgress("", 0, 3)
    completed_values = [event.checks_completed for event in events]
    assert completed_values[0] == 0
    assert completed_values[-1] == 3
    assert max(event.checks_total for event in events) == 3
    assert any(event.checks_completed == 1 for event in events)
    assert any(event.checks_completed == 2 for event in events)


def test_run_all_checks_emits_progress_parallel(tmp_path: Path, monkeypatch):
    reports, events = collect_progress(tmp_path, monkeypatch, parallel=True)
    assert {report.tool_id for report in reports} == {"a.tool", "b.tool", "c.tool"}
    assert events[0] == RunProgress("", 0, 3)
    assert events[-1].checks_completed == 3
    assert events[-1].checks_total == 3
    assert any(event.checks_completed > 0 and event.checks_completed < 3 for event in events)
