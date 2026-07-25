"""Application service layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.baseline import load_baseline, save_baseline
from shipgate.catalog.loader import CatalogLoader
from shipgate.config.loader import ProjectConfigLoader
from shipgate.domain.modes import RunMode
from shipgate.domain.reports import RunReport, report_json_schema
from shipgate.domain.run_command import RunCommand
from shipgate.gates.core import GateCatalogMerger
from shipgate.gates.init import init_gate
from shipgate.gates.paths import gates_lib_path
from shipgate.planning.core.checks import list_project_checks
from shipgate.project.configs import diff_configs, list_resolved_configs, sync_configs
from shipgate.project.init import init_project
from shipgate.project.suggest import suggest_tools
from shipgate.runtime.executor import Executor
from shipgate.runtime.install import install_suite
from shipgate.runtime.lockfile import write_lockfile
from shipgate.runtime.run_session import RunProgress, RunSession

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog

__all__ = ["InstallCommand", "RunCommand", "RunProgress", "ShipGateApp"]


@dataclass(frozen=True)
class InstallCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None


class ShipGateApp:
    def __init__(
        self,
        *,
        catalog: Catalog | None = None,
        executor: Executor | None = None,
    ) -> None:
        self._custom_catalog = catalog is not None
        self._base_catalog = catalog or CatalogLoader.load()
        self._executor_is_default = executor is None
        self.executor = executor or Executor()

    def _catalog_for(self, project_root: Path) -> Catalog:
        base = (
            CatalogLoader.load(project_root=project_root)
            if not self._custom_catalog
            else self._base_catalog
        )
        return GateCatalogMerger.merge(base, project_root)

    def _run_session(self, project_root: Path) -> RunSession:
        return RunSession(
            catalog=self._catalog_for(project_root),
            executor=self.executor,
            executor_is_default=self._executor_is_default,
        )

    def install(self, command: InstallCommand) -> int:
        catalog = self._catalog_for(command.project_root)
        project = ProjectConfigLoader.load(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        suite_id = command.suite or project.suite or "standard"
        install_suite(command.project_root, suite_id, catalog, force=False)
        return 0

    def update(self, command: InstallCommand) -> int:
        catalog = self._catalog_for(command.project_root)
        project = ProjectConfigLoader.load(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        suite_id = command.suite or project.suite or "standard"
        install_suite(command.project_root, suite_id, catalog, force=True)
        return 0

    def check(self, command: RunCommand) -> int:
        exit_code, _report = self.run_suite(command, RunMode.CHECK)
        return exit_code

    def format(self, command: RunCommand) -> int:
        exit_code, _report = self.run_suite(command, RunMode.APPLY)
        return exit_code

    def run_suite(
        self,
        command: RunCommand,
        mode: RunMode,
        *,
        run_id: str | None = None,
        on_progress=None,
        write_reports: bool = True,
        emit_failure_output: bool = True,
    ) -> tuple[int, RunReport]:
        return self._run_session(command.project_root).run(
            command,
            mode,
            run_id=run_id,
            on_progress=on_progress,
            write_reports=write_reports,
            emit_failure_output=emit_failure_output,
        )

    def list_suites(self) -> str:
        catalog = self._base_catalog
        return "\n".join(sorted(catalog.suites.keys())) + "\n"

    def list_tools(self, *, tag: str | None = None) -> str:
        tools = self._base_catalog.tools
        names = sorted(
            tool_id for tool_id, tool in tools.items() if tag is None or tag in tool.tags
        )
        return "\n".join(names) + ("\n" if names else "")

    def list_checks(self, project_root: Path | None = None) -> str:
        if project_root is None:
            from shipgate.paths import find_project_root

            project_root = find_project_root()
        project = ProjectConfigLoader.load(project_root=project_root)
        catalog = self._catalog_for(project_root)
        checks = list_project_checks(project, catalog)
        return "\n".join(checks) + ("\n" if checks else "")

    @staticmethod
    def schema() -> str:
        return json.dumps(report_json_schema(), indent=2) + "\n"

    @staticmethod
    def serve(
        project_root: Path,
        host: str = "127.0.0.1",
        port: int = 8765,
        *,
        open_browser: bool = False,
    ) -> int:
        from shipgate.frontend.server import serve

        serve(project_root, host=host, port=port, open_browser=open_browser)
        return 0

    @staticmethod
    def lock(project_root: Path) -> int:
        manifest = project_root / ".shipgate" / "tools" / "manifest.json"
        packages: dict[str, str] = {}
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            packages = {
                **{k: str(v) for k, v in data.get("packages", {}).items()},
                **{k: str(v) for k, v in data.get("binaries", {}).items()},
            }
        write_lockfile(project_root / ".shipgate" / "lock.json", packages)
        return 0

    def baseline_update(self, command: RunCommand) -> int:
        exit_code, report = self.run_suite(command, RunMode.CHECK)
        if exit_code != 0:
            return exit_code
        project = ProjectConfigLoader.load(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        baseline_report = RunReport(
            run_id="baseline",
            suite=project.suite,
            mode="check",
            status="passed",
            reports=report.reports,
        )
        save_baseline(command.project_root, baseline_report)
        return 0

    @staticmethod
    def baseline_show(project_root: Path) -> str:
        baseline = load_baseline(project_root)
        if baseline is None:
            return "no baseline\n"
        return json.dumps(baseline.to_dict(), indent=2) + "\n"

    def run_batch(self, project_root: Path, batch_path: Path) -> int:
        from shipgate.batch import load_batch_file

        requests = load_batch_file(batch_path)
        worst = 0
        for req in requests:
            cmd = RunCommand(
                project_root=project_root,
                check=req.runnable,
                target=req.target,
                extra_args=req.extra_args,
            )
            code = self.format(cmd) if req.mode == RunMode.APPLY else self.check(cmd)
            worst = max(worst, code)
        return worst

    @staticmethod
    def gates_init(project_root: Path, name: str) -> str:
        path = init_gate(project_root, name)
        return f"created gate: {path}\n"

    @staticmethod
    def gates_lib_path() -> str:
        return f"{gates_lib_path()}\n"

    def init(
        self,
        project_root: Path,
        *,
        configs_only: bool = False,
        mode: str = "yaml",
        project_env: Path | None = None,
    ) -> str:
        path = init_project(
            project_root,
            configs_only=configs_only,
            mode=mode,
            project_env=project_env,
        )
        suggestions = suggest_tools(project_root, self._catalog_for(project_root))
        suggestion_text = ""
        if suggestions:
            suggestion_text = "\n".join(suggestions) + "\n"
        if configs_only:
            return suggestion_text + "scaffolded .shipgate configs\n"
        if mode == "pyproject":
            return suggestion_text + f"updated {path}\n"
        return suggestion_text + f"created {path}\n"

    def configs_sync(self, project_root: Path) -> str:
        created = sync_configs(project_root, self._catalog_for(project_root))
        if not created:
            return "no missing configs\n"
        lines = [f"created {path.relative_to(project_root)}" for path in created]
        return "\n".join(lines) + "\n"

    def configs_list(
        self,
        project_root: Path,
        *,
        suite: str | None = None,
    ) -> str:
        project = ProjectConfigLoader.load(project_root=project_root)
        catalog = self._catalog_for(project_root)
        lines = list_resolved_configs(
            project_root,
            catalog,
            project,
            suite=suite,
        )
        return "\n".join(lines) + ("\n" if lines else "")

    def configs_diff(self, project_root: Path, tool_id: str | None = None) -> str:
        catalog = self._catalog_for(project_root)
        return diff_configs(project_root, catalog, tool_id=tool_id)
