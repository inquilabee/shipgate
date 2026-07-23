import sys
from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.planning.workflow import PlannedCheck
from shipgate.runtime.session.check_planner import prepare_check
from shipgate.runtime.session.context import RunCommand, RunContext


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
    catalog = load_catalog()
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
    catalog = load_catalog()
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
    catalog = load_catalog()
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
    assert prepared.report.status == "passed"
    assert prepared.report.exit_code == 0
    assert prepared.report.extra["skipped"] == "no matching files in scope"


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
    catalog = load_catalog()
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


def test_prepare_check_short_circuits_when_incremental_clean(tmp_path: Path):
    from shipgate.planning.incremental import RunScopeSession

    catalog = load_catalog()
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
    assert prepared.report.extra["skipped"] == "no matching files in scope"
