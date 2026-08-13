from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.domain.run_command import RunCommand
from shipgate.planning.utils.incremental import RunScopeSession
from shipgate.planning.workflow import SelectedTool
from shipgate.runtime.session.check_resolver import prepare_run
from shipgate.runtime.session.context import RunContext


class ImportLinterPrepare:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path

    def run(self):
        catalog = CatalogLoader.load()
        selected = SelectedTool(tool_id="import-linter.check", mode=RunMode.CHECK)
        command = RunCommand(
            project_root=self.tmp_path,
            target=self.tmp_path,
            check="import-linter.check",
        )
        return prepare_run(
            selected=selected,
            command=command,
            context=self.context(selected),
            catalog=catalog,
        )

    def context(self, selected: SelectedTool) -> RunContext:
        return RunContext(
            project=ProjectConfig(env="system", target=Path()),
            project_root=self.tmp_path.resolve(),
            suite_id=selected.tool_id,
            selected_tools=(selected,),
            environment=ExecutionEnvironment(kind="system", root=None, env={}),
            parallel=False,
            fail_fast=False,
            scope_session=RunScopeSession(
                project_root=self.tmp_path.resolve(),
                changed_only=False,
                since=None,
            ),
        )


def test_prepare_run_skips_import_linter_without_importable_package(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fresh"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    prepared = ImportLinterPrepare(tmp_path).run()
    assert prepared.request is None
    assert prepared.report is not None
    assert prepared.report.status == "skipped"
    assert prepared.report.extra["skipped"] == "no importable package in project layout"


def test_prepare_run_runs_import_linter_with_src_package(tmp_path: Path):
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    prepared = ImportLinterPrepare(tmp_path).run()
    assert prepared.report is None
    assert prepared.request is not None
    assert prepared.request.runnable == "import-linter.check"


def test_prepare_run_runs_import_linter_with_flat_package(tmp_path: Path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "service.py").write_text("x = 1\n", encoding="utf-8")
    prepared = ImportLinterPrepare(tmp_path).run()
    assert prepared.report is None
    assert prepared.request is not None
    assert prepared.request.runnable == "import-linter.check"
