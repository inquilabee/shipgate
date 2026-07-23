import sys
from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.domain.run_command import RunCommand
from shipgate.planning.workflow import PlannedCheck
from shipgate.runtime.session.check_planner import prepare_check
from shipgate.runtime.session.context import RunContext


def make_run_context(tmp_path: Path, planned: PlannedCheck) -> RunContext:
    from shipgate.planning.incremental import RunScopeSession

    return RunContext(
        project=ProjectConfig(env="system", target=Path()),
        project_root=tmp_path.resolve(),
        suite_id=planned.tool_id,
        planned_checks=(planned,),
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
        parallel=False,
        fail_fast=False,
        scope_session=RunScopeSession(
            project_root=tmp_path.resolve(),
            changed_only=False,
            since=None,
        ),
    )


def test_prepare_check_builds_resolved_request(tmp_path: Path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="ruff.lint", mode=RunMode.CHECK)
    command = RunCommand(
        project_root=tmp_path,
        target=tmp_path,
        check="ruff.lint",
        extra_args=("--select", "F401"),
        verbose=True,
    )
    prepared = prepare_check(
        planned=planned,
        command=command,
        context=make_run_context(tmp_path, planned),
        catalog=catalog,
    )
    assert prepared.report is None
    assert prepared.request is not None
    assert prepared.request.runnable == "ruff.lint"
    assert prepared.request.mode == RunMode.CHECK
    assert prepared.request.options.check is True
    assert prepared.request.options.verbose is True
    assert prepared.request.extra_args == ("--select", "F401")
    assert prepared.request.options.paths
    assert prepared.request.options.config


def test_prepare_check_apply_mode_sets_check_false(tmp_path: Path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="ruff.format", mode=RunMode.APPLY)
    command = RunCommand(project_root=tmp_path, target=tmp_path, check="ruff.format")
    prepared = prepare_check(
        planned=planned,
        command=command,
        context=make_run_context(tmp_path, planned),
        catalog=catalog,
    )
    assert prepared.request is not None
    assert prepared.request.options.check is False


def test_prepare_check_skips_when_no_matching_files(tmp_path: Path):
    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="yamllint.check", mode=RunMode.CHECK)
    command = RunCommand(project_root=tmp_path, target=tmp_path, check="yamllint.check")
    prepared = prepare_check(
        planned=planned,
        command=command,
        context=make_run_context(tmp_path, planned),
        catalog=catalog,
    )
    assert prepared.request is None
    assert prepared.report is not None
    assert prepared.report.status == "skipped"
    assert prepared.report.exit_code == 0
    assert prepared.report.extra["skipped"] == "no matching files in scope"


def test_options_for_mode_apply_preserves_exclude(tmp_path: Path):
    from shipgate.domain.catalog import CliOptionDefinition, ToolDefinition
    from shipgate.planning.check_planner import CheckPlanner
    from shipgate.planning.incremental import RunScopeSession

    tool = ToolDefinition(
        id="demo.format",
        executable="demo",
        modes=(RunMode.CHECK, RunMode.APPLY),
        cli={
            "paths": CliOptionDefinition(style="positional"),
            "exclude": CliOptionDefinition(flag="--exclude", style="repeated"),
        },
    )
    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id=tool.id, mode=RunMode.APPLY)
    context = make_run_context(tmp_path, planned)
    planner = CheckPlanner(
        project_root=context.project_root,
        project=context.project,
        catalog=catalog,
        scope_session=RunScopeSession(
            project_root=tmp_path.resolve(),
            changed_only=False,
            since=None,
        ),
        environment=context.environment,
    )
    options = planner._options_for_mode(
        planned,
        tool,
        paths=(Path("a.py"),),
        config_paths=(),
        exclude=("vendor",),
        command=RunCommand(project_root=tmp_path),
    )
    assert options.exclude == ("vendor",)
    assert options.check is False


def test_prepare_check_ty_includes_project_python(tmp_path: Path):
    if sys.platform == "win32":
        scripts = tmp_path / ".venv" / "Scripts"
        scripts.mkdir(parents=True)
        (scripts / "python.exe").write_text("", encoding="utf-8")
    else:
        bindir = tmp_path / ".venv" / "bin"
        bindir.mkdir(parents=True)
        (bindir / "python").write_text("", encoding="utf-8")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="ty.check", mode=RunMode.CHECK)
    command = RunCommand(project_root=tmp_path, target=tmp_path, check="ty.check")
    prepared = prepare_check(
        planned=planned,
        command=command,
        context=make_run_context(tmp_path, planned),
        catalog=catalog,
    )
    assert prepared.request is not None
    assert prepared.request.options.python == ".venv"


def test_check_planner_reuses_scope_resolver(tmp_path: Path):
    from shipgate.planning.check_planner import CheckPlanner

    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="ruff.lint", mode=RunMode.CHECK)
    context = make_run_context(tmp_path, planned)
    planner = CheckPlanner(
        project_root=context.project_root,
        project=context.project,
        catalog=catalog,
        scope_session=context.scope_session,
        environment=context.environment,
    )
    assert planner._scope_resolver is not None
    first = planner._scope_resolver
    command = RunCommand(project_root=tmp_path, target=tmp_path, check="ruff.lint")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    planner.prepare(planned, command)
    assert planner._scope_resolver is first


def test_build_run_report_treats_skipped_as_non_failure():
    from shipgate.domain.modes import RunMode
    from shipgate.domain.reports import CheckReport
    from shipgate.runtime.session.check_runner import build_run_report

    report = build_run_report(
        run_id="20260101T000000Z-abc123",
        suite_id="standard",
        mode=RunMode.CHECK,
        check_reports=[
            CheckReport(
                check_id="ruff.lint",
                tool_id="ruff.lint",
                status="passed",
                exit_code=0,
            ),
            CheckReport(
                check_id="yamllint.check",
                tool_id="yamllint.check",
                status="skipped",
                exit_code=0,
                extra={"skipped": "no matching files in scope"},
            ),
        ],
    )
    assert report.status == "passed"


def test_prepare_check_short_circuits_when_incremental_clean(tmp_path: Path):
    from shipgate.planning.incremental import RunScopeSession

    catalog = CatalogLoader.load()
    planned = PlannedCheck(tool_id="ruff.lint", mode=RunMode.CHECK)
    command = RunCommand(
        project_root=tmp_path,
        target=tmp_path,
        check="ruff.lint",
        changed_only=True,
    )
    context = RunContext(
        project=ProjectConfig(env="system", target=Path(), changed_only=True),
        project_root=tmp_path.resolve(),
        suite_id=planned.tool_id,
        planned_checks=(planned,),
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
        parallel=False,
        fail_fast=False,
        scope_session=RunScopeSession(
            project_root=tmp_path.resolve(),
            changed_only=True,
            since=None,
            _incremental_clean=True,
        ),
    )
    prepared = prepare_check(
        planned=planned,
        command=command,
        context=context,
        catalog=catalog,
    )
    assert prepared.request is None
    assert prepared.report is not None
    assert prepared.report.status == "skipped"
    assert prepared.report.extra["skipped"] == "no matching files in scope"
