"""Config path resolution for adapter."""

from pathlib import Path

from shipgate.config.core.pyproject import PyprojectPolicyLoader
from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.project import ProjectConfig
from shipgate.paths import contained_child_or_none


class ConfigPathResolver:
    """Resolve tool configuration file paths for a project root."""

    def __init__(
        self,
        tool: ToolDefinition,
        project: ProjectConfig,
        project_root: Path,
    ) -> None:
        self._tool = tool
        self._project = project
        self._project_root = project_root
        self._bundled = self.bundled_configs_root()

    @classmethod
    def resolve(
        cls,
        tool: ToolDefinition,
        project: ProjectConfig,
        project_root: Path,
    ) -> tuple[Path, ...]:
        return cls(tool, project, project_root)._resolve()

    @staticmethod
    def bundled_configs_root() -> Path:
        return Path(__file__).resolve().parents[1] / "catalog" / "bundled"

    def _resolve(self) -> tuple[Path, ...]:
        config = self._tool.configuration
        if self._project.config_mode == "bundled" and config.bundled:
            bundled = contained_child_or_none(self._bundled, config.bundled)
            return (bundled,) if bundled is not None else ()

        if self._project.config_mode == "auto":
            return self._resolve_auto()

        if path := self._first_discover_match(config.discover):
            return (path,)
        return self._bundled_fallback()

    def _resolve_auto(self) -> tuple[Path, ...]:
        config = self._tool.configuration
        if path := self._discover_repo_native(config.discover):
            return (path,)
        if path := self._first_discover_match(config.discover):
            return (path,)
        return self._bundled_fallback()

    def _discover_repo_native(self, patterns: tuple[str, ...]) -> Path | None:
        for pattern in patterns:
            if self._is_shipgate_scaffold_path(pattern):
                continue
            if path := self._match_candidate(pattern):
                return path
        return None

    def _first_discover_match(self, patterns: tuple[str, ...]) -> Path | None:
        for pattern in patterns:
            if path := self._match_candidate(pattern):
                return path
        return None

    @staticmethod
    def _is_shipgate_scaffold_path(pattern: str) -> bool:
        normalized = pattern.replace("\\", "/")
        return normalized.startswith(".shipgate/configs/")

    def _match_candidate(self, pattern: str) -> Path | None:
        candidate = contained_child_or_none(self._project_root, pattern)
        return (
            None
            if candidate is None or not candidate.is_file()
            else self._file_or_pyproject(candidate)
        )

    def _file_or_pyproject(self, candidate: Path) -> Path | None:
        return self._match_pyproject(candidate) if candidate.name == "pyproject.toml" else candidate

    def _match_pyproject(self, path: Path) -> Path | None:
        section = self._tool.configuration.pyproject_section
        if not section:
            return None
        try:
            PyprojectPolicyLoader.load_section(path, section)
        except (KeyError, TypeError):
            return None
        return path

    def _bundled_fallback(self) -> tuple[Path, ...]:
        config = self._tool.configuration
        if self._project.config_mode != "auto" or not config.bundled:
            return ()
        bundled = contained_child_or_none(self._bundled, config.bundled)
        return (bundled,) if bundled is not None else ()


def resolve_config_paths(
    tool: ToolDefinition,
    project: ProjectConfig,
    project_root: Path,
) -> tuple[Path, ...]:
    return ConfigPathResolver.resolve(tool, project, project_root)
