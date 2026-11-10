"""``shipgate doctor``: what a run would do in this project, and why. Read-only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.domain.modes import RunMode
from shipgate.paths import PROJECT_CATALOG_DIR, PROJECT_CONFIGS_DIR, SHIPGATE_DIR, SHIPGATE_YAML
from shipgate.planning.core.scope_resolver import ScopeResolver
from shipgate.planning.utils.git_visible import GitVisibleFiles
from shipgate.planning.utils.gitignore import exclusion_reason, load_gitignore_spec
from shipgate.planning.workflow import resolve_runnables, suite_execution_flags
from shipgate.project.layout.types import SKIP_DIR_NAMES

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition
    from shipgate.domain.project import ProjectConfig

POLICY_PATHS = (
    SHIPGATE_YAML,
    PROJECT_CONFIGS_DIR,
    PROJECT_CATALOG_DIR,
    SHIPGATE_DIR / "allowlists",
)
LOCKFILE = SHIPGATE_DIR / "lock.json"


@dataclass(frozen=True)
class ToolState:
    tool_id: str
    pinned: str
    locked: str | None
    installed: str | None

    @property
    def status(self) -> str:
        return (
            "not installed"
            if self.installed is None
            else "not locked"
            if self.locked is None
            else "ok"
            if self.installed == self.locked == self.pinned
            else "differs"
        )

    def render(self) -> str:
        return (
            f"  {self.tool_id}  pinned {self.pinned}  locked {self.locked or '-'}  "
            f"installed {self.installed or '-'}  {self.status}"
        )


@dataclass(frozen=True)
class DoctorReport:
    suite_id: str
    parallel: bool
    fail_fast: bool
    changed_only: bool
    since: str | None
    target: str
    scope: tuple[tuple[str, str | None], ...]
    policy_files: tuple[tuple[str, str], ...]
    tools: tuple[ToolState, ...]

    def render(self) -> str:
        lines = [*self.run_lines(), *self.scope_lines(), *self.policy_lines(), *self.tool_lines()]
        return "\n".join(lines) + "\n"

    def run_lines(self) -> list[str]:
        incremental = f"yes (since {self.since})" if self.since else str(self.changed_only).lower()
        return [
            f"suite: {self.suite_id} (parallel: {self.parallel}, fail-fast: {self.fail_fast})",
            f"changed-only: {incremental}",
        ]

    def scope_lines(self) -> list[str]:
        included = ", ".join(name for name, why in self.scope if why is None)
        return [
            f"scope target: {self.target}",
            f"  in scope: {included or '(nothing)'}",
            *(f"  out: {name}  ({why})" for name, why in self.scope if why is not None),
        ]

    def policy_lines(self) -> list[str]:
        return ["policy files:", *(f"  {path}  {state}" for path, state in self.policy_files)]

    def tool_lines(self) -> list[str]:
        return ["tools:", *(tool.render() for tool in self.tools)]


class ProjectDoctor:
    """Builds a ``DoctorReport`` from the same resolvers a real run uses."""

    def __init__(
        self,
        project_root: Path,
        project: ProjectConfig,
        catalog: Catalog,
        *,
        installed_version: Callable[[ToolDefinition], str | None],
    ) -> None:
        self.root = project_root.resolve()
        self.project = project
        self.catalog = catalog
        self._installed_version = installed_version

    def report(self) -> DoctorReport:
        suite_id, selected = resolve_runnables(
            mode=RunMode.CHECK, project=self.project, catalog=self.catalog
        )
        parallel, fail_fast = suite_execution_flags(
            self.catalog, suite_id, self.project, RunMode.CHECK
        )
        target, scope = self.scope_entries()
        return DoctorReport(
            suite_id=suite_id,
            parallel=parallel,
            fail_fast=fail_fast,
            changed_only=self.project.changed_only,
            since=self.project.since,
            target=target,
            scope=scope,
            policy_files=self.policy_files(),
            tools=self.tool_states([item.tool_id for item in selected]),
        )

    def scope_entries(self) -> tuple[str, tuple[tuple[str, str | None], ...]]:
        resolver = ScopeResolver(self.root)
        scope = resolver.resolve(self.project)
        target = resolver.resolve_scope_target(scope)
        spec = load_gitignore_spec(self.root) if scope.respect_gitignore else None
        visible = GitVisibleFiles.load(self.root)
        children = sorted(target.iterdir()) if target.is_dir() else [target]
        entries = tuple(
            (
                child.name,
                exclusion_reason(
                    self.root,
                    child,
                    extra_excludes=scope.exclude,
                    spec=spec,
                    respect_gitignore=scope.respect_gitignore,
                    git_visible=visible,
                )
                or ("skipped directory name" if child.name in SKIP_DIR_NAMES else None),
            )
            for child in children
        )
        return str(target.relative_to(self.root) or "."), entries

    def policy_files(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (path.as_posix(), self.git_state(path.as_posix()))
            for path in POLICY_PATHS
            if (self.root / path).exists()
        )

    def git_state(self, rel: str) -> str:
        if not (self.root / ".git").is_dir():
            return "not a git repo"
        if run_command(["git", "ls-files", "--", rel], cwd=self.root).stdout.strip():
            return "tracked"
        ignored = run_command(["git", "check-ignore", "-q", "--", rel], cwd=self.root).returncode
        return "git-ignored" if ignored == 0 else "untracked (not committed)"

    def tool_states(self, tool_ids: list[str]) -> tuple[ToolState, ...]:
        locked = self.locked_versions()
        states: list[ToolState] = []
        for tool_id in tool_ids:
            tool = self.catalog.get_tool(tool_id)
            if tool.install is None:
                continue
            name = (
                tool.install.package
                if tool.install.manager == "python"
                else tool.install.binary or tool.install.package
            )
            installed = self._installed_version(tool)
            states.append(
                ToolState(
                    tool_id=tool_id,
                    pinned=str(tool.install.version).lstrip("v"),
                    locked=(locked.get(name) or "").lstrip("v") or None,
                    installed=installed.lstrip("v") if installed else None,
                )
            )
        return tuple(states)

    def locked_versions(self) -> dict[str, str]:
        try:
            data = json.loads((self.root / LOCKFILE).read_text(encoding="utf-8"))
            return {str(name): str(version) for name, version in data["packages"].items()}
        except (OSError, ValueError, KeyError, AttributeError):
            return {}
