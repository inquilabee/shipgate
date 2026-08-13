"""Project config loader."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.config.core import (
    ProjectConfigParser,
    PyprojectPolicyLoader,
    ScopeSourceResolver,
)
from shipgate.config.discovery import discover_yaml_config_path
from shipgate.config.merge import deep_merge_config
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.domain.project import ProjectConfig
from shipgate.errors import ConfigError
from shipgate.paths import (
    PROJECT_CACHE_ENV,
    find_cached_policy,
    find_project_root,
    read_cached_policy,
)

if TYPE_CHECKING:
    from pathlib import Path


class ProjectConfigLoader:
    """Load layered project policy from YAML and pyproject.toml into ``ProjectConfig``.

    Discovers policy sources, merges overlays, resolves scope sources, and orchestrates parse.
    """

    def __init__(self, *, project_root: Path, config_path: Path | None = None) -> None:
        self._project_root = project_root
        self._config_path = config_path

    @classmethod
    def load(
        cls,
        *,
        config_path: Path | None = None,
        project_root: Path | None = None,
    ) -> ProjectConfig:
        root = (project_root or find_project_root()).resolve()
        return cls(project_root=root, config_path=config_path)._load()

    def _load(self) -> ProjectConfig:
        return (
            self._load_explicit(self._config_path.resolve())
            if self._config_path is not None
            else self._load_layered()
        )

    def _load_explicit(self, path: Path) -> ProjectConfig:
        if self._is_toml_policy_path(path):
            section = PyprojectPolicyLoader.load_shipgate_section(path)
            return (
                self._parse_raw(section, path, pyproject_path=path) if section else ProjectConfig()
            )
        if not path.is_file():
            raise ConfigError(f"config file not found: {path}", path=str(path))
        raw = load_yaml_mapping(path, error_cls=ConfigError)
        if not raw:
            return ProjectConfig()
        pyproject_path = PyprojectPolicyLoader.discover_path(self._project_root)
        return self._parse_raw(raw, path, pyproject_path=pyproject_path)

    def _load_layered(self) -> ProjectConfig:
        policy = self._resolve_policy()
        yaml_path = discover_yaml_config_path(self._project_root)
        pyproject_path = PyprojectPolicyLoader.discover_path(self._project_root)
        yaml_raw = self._load_yaml_raw(yaml_path)
        pyproject_raw = (
            PyprojectPolicyLoader.load_shipgate_section(pyproject_path)
            if pyproject_path is not None
            else None
        )
        return self._build_layered_config(
            policy=policy,
            yaml_path=yaml_path,
            yaml_raw=yaml_raw,
            pyproject_path=pyproject_path,
            pyproject_raw=pyproject_raw,
        )

    @staticmethod
    def _load_yaml_raw(yaml_path: Path | None) -> dict[str, object] | None:
        if yaml_path is None or not yaml_path.is_file():
            return None
        loaded = load_yaml_mapping(yaml_path, error_cls=ConfigError)
        return loaded or None

    def _build_layered_config(
        self,
        *,
        policy: str,
        yaml_path: Path | None,
        yaml_raw: dict[str, object] | None,
        pyproject_path: Path | None,
        pyproject_raw: dict[str, object] | None,
    ) -> ProjectConfig:
        if yaml_raw and pyproject_raw:
            if policy == "pyproject":
                return (
                    ProjectConfig()
                    if pyproject_path is None
                    else self._parse_raw(
                        pyproject_raw, pyproject_path, pyproject_path=pyproject_path
                    )
                )
            merged = deep_merge_config(pyproject_raw, yaml_raw)
            config_path = yaml_path
            return (
                ProjectConfig()
                if config_path is None
                else self._parse_raw(merged, config_path, pyproject_path=pyproject_path)
            )
        return (
            self._parse_raw(yaml_raw, yaml_path, pyproject_path=pyproject_path)
            if yaml_raw and yaml_path is not None
            else (
                self._parse_raw(pyproject_raw, pyproject_path, pyproject_path=pyproject_path)
                if pyproject_raw and pyproject_path is not None
                else ProjectConfig()
            )
        )

    def _parse_raw(
        self,
        raw: dict[str, object],
        path: Path,
        *,
        pyproject_path: Path | None,
    ) -> ProjectConfig:
        prepared = dict(raw)
        scopes_raw = prepared.get("scopes")
        if scopes_raw is not None and isinstance(scopes_raw, dict):
            scopes_map = {str(key): item for key, item in scopes_raw.items()}
            prepared["scopes"] = ScopeSourceResolver(
                project_root=self._project_root,
                pyproject_path=pyproject_path,
                config_path=path,
            ).resolve(scopes_map)
        return ProjectConfigParser.parse(prepared, path)

    def _resolve_policy(self) -> str:
        cached = read_cached_policy(self._project_root / PROJECT_CACHE_ENV)
        if cached is not None:
            return cached
        walked = find_cached_policy(self._project_root)
        return walked if walked is not None else "yaml"

    @staticmethod
    def _is_toml_policy_path(path: Path) -> bool:
        return ".toml" in path.name
