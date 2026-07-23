"""Project config loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shipgate.config.discovery import discover_yaml_config_path
from shipgate.config.merge import deep_merge_config
from shipgate.config.pyproject import discover_pyproject_path, load_shipgate_section
from shipgate.config.schema import (
    ALLOWED_CONFIG_MODES,
    ALLOWED_ENV_VALUES,
    ALLOWED_ERROR_FORMATS,
    ALLOWED_TOP_LEVEL_KEYS,
)
from shipgate.config.scope_sources import resolve_scope_sources
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.domain.project import CheckBinding, ProjectConfig, Scope
from shipgate.errors import ConfigError
from shipgate.paths import (
    find_cached_policy,
    find_project_root,
    project_root_cache_env_path,
    read_cached_policy,
)


def load_config(
    *,
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> ProjectConfig:
    root = (project_root or find_project_root()).resolve()
    if config_path is not None:
        return ProjectConfigLoader.load_explicit_config(config_path.resolve(), root)
    return ProjectConfigLoader.load_layered_config(root)


class ProjectConfigLoader:
    @staticmethod
    def load_explicit_config(path: Path, project_root: Path) -> ProjectConfig:
        if ProjectConfigLoader.is_toml_policy_path(path):
            section = load_shipgate_section(path)
            if not section:
                return ProjectConfig()
            return ProjectConfigLoader.parse_config_dict(
                section,
                path,
                project_root=project_root,
                pyproject_path=path,
            )
        if not path.is_file():
            raise ConfigError(f"config file not found: {path}", path=str(path))
        raw = load_yaml_mapping(path, error_cls=ConfigError)
        if not raw:
            return ProjectConfig()
        pyproject_path = discover_pyproject_path(project_root)
        return ProjectConfigLoader.parse_config_dict(
            raw,
            path,
            project_root=project_root,
            pyproject_path=pyproject_path,
        )

    @staticmethod
    def load_layered_config(project_root: Path) -> ProjectConfig:
        policy = ProjectConfigLoader.resolve_policy(project_root)
        yaml_path = discover_yaml_config_path(project_root)
        pyproject_path = discover_pyproject_path(project_root)
        yaml_raw = ProjectConfigLoader.load_yaml_raw(yaml_path)
        pyproject_raw = (
            load_shipgate_section(pyproject_path) if pyproject_path is not None else None
        )
        return ProjectConfigLoader.build_layered_config(
            project_root=project_root,
            policy=policy,
            yaml_path=yaml_path,
            yaml_raw=yaml_raw,
            pyproject_path=pyproject_path,
            pyproject_raw=pyproject_raw,
        )

    @staticmethod
    def load_yaml_raw(yaml_path: Path | None) -> dict[str, Any] | None:
        if yaml_path is None or not yaml_path.is_file():
            return None
        loaded = load_yaml_mapping(yaml_path, error_cls=ConfigError)
        return loaded or None

    @staticmethod
    def build_layered_config(
        *,
        project_root: Path,
        policy: str,
        yaml_path: Path | None,
        yaml_raw: dict[str, Any] | None,
        pyproject_path: Path | None,
        pyproject_raw: dict[str, Any] | None,
    ) -> ProjectConfig:
        if yaml_raw and pyproject_raw:
            merged = deep_merge_config(pyproject_raw, yaml_raw)
            config_path = yaml_path if policy == "yaml" else pyproject_path
            if config_path is None:
                return ProjectConfig()
            return ProjectConfigLoader.parse_config_dict(
                merged,
                config_path,
                project_root=project_root,
                pyproject_path=pyproject_path,
            )
        if yaml_raw and yaml_path is not None:
            return ProjectConfigLoader.parse_config_dict(
                yaml_raw,
                yaml_path,
                project_root=project_root,
                pyproject_path=pyproject_path,
            )
        if pyproject_raw and pyproject_path is not None:
            return ProjectConfigLoader.parse_config_dict(
                pyproject_raw,
                pyproject_path,
                project_root=project_root,
                pyproject_path=pyproject_path,
            )
        return ProjectConfig()

    @staticmethod
    def resolve_policy(project_root: Path) -> str:
        cached = read_cached_policy(project_root_cache_env_path(project_root))
        if cached is not None:
            return cached
        walked = find_cached_policy(project_root)
        if walked is not None:
            return walked
        return "yaml"

    @staticmethod
    def is_toml_policy_path(path: Path) -> bool:
        return ".toml" in path.name

    @staticmethod
    def parse_config_dict(
        raw: dict[str, Any],
        path: Path,
        *,
        project_root: Path,
        pyproject_path: Path | None,
    ) -> ProjectConfig:
        validate_top_level_keys(raw, path)
        env = require_allowed(raw.get("env", "managed"), ALLOWED_ENV_VALUES, "env", path)
        error_format_raw = raw.get("error-format")
        error_format = None
        if error_format_raw is not None:
            error_format = require_allowed(
                error_format_raw,
                ALLOWED_ERROR_FORMATS,
                "error-format",
                path,
            )
        config_mode = parse_config_mode(raw, path)
        checks, check_bindings = parse_checks(raw, path)
        scopes_raw = raw.get("scopes")
        if scopes_raw is not None and isinstance(scopes_raw, dict):
            scopes_raw = resolve_scope_sources(
                scopes_raw,
                project_root=project_root,
                pyproject_path=pyproject_path,
                config_path=path,
            )
        scopes = parse_scopes(scopes_raw, path)
        allowlists = parse_allowlists(raw.get("allowlists"), path)
        suite = raw.get("suite", "standard")
        if suite is not None:
            suite = str(suite)
        workflow = raw.get("workflow")
        if workflow is not None:
            workflow = str(workflow)
        return ProjectConfig(
            suite=suite,
            workflow=workflow,
            env=env,
            target=Path(raw.get("target", ".")),
            error_format=error_format,
            config_mode=config_mode,
            checks=checks,
            check_bindings=check_bindings,
            scopes=scopes,
            auto_install=bool(raw.get("auto-install", False)),
            parallel=bool(raw.get("parallel", False)),
            fail_fast=bool(raw.get("fail-fast", False)),
            changed_only=bool(raw.get("changed-only", False)),
            since=str(raw["since"]) if raw.get("since") is not None else None,
            allowlists=allowlists,
        )


def validate_top_level_keys(raw: dict, path: Path) -> None:
    unknown = set(raw) - ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        raise ConfigError(
            f"unknown config key(s): {', '.join(sorted(unknown))}",
            path=str(path),
        )


def require_allowed(
    value: object,
    allowed: set[str] | frozenset[str],
    label: str,
    path: Path,
) -> str:
    if value not in allowed:
        raise ConfigError(f"invalid {label}: {value!r}", path=str(path))
    return str(value)


def parse_checks(raw: dict, path: Path) -> tuple[tuple[str, ...], tuple[CheckBinding, ...]]:
    checks_raw = raw.get("checks", []) or []
    if isinstance(checks_raw, list):
        return tuple(str(c) for c in checks_raw), ()
    if isinstance(checks_raw, dict):
        bindings: list[CheckBinding] = []
        for runnable, value in checks_raw.items():
            runnable_id = str(runnable)
            scope_name = None
            threshold = None
            if isinstance(value, dict):
                scope_name = value.get("scope")
                if scope_name is not None:
                    scope_name = str(scope_name)
                threshold_raw = value.get("threshold")
                if threshold_raw is not None:
                    threshold = str(threshold_raw)
            bindings.append(
                CheckBinding(
                    runnable=runnable_id,
                    scope=scope_name,
                    threshold=threshold,
                )
            )
        return (), tuple(bindings)
    raise ConfigError("checks must be a list or mapping", path=str(path))


def parse_config_mode(raw: dict, path: Path) -> str:
    configs = raw.get("configs", {}) or {}
    if not isinstance(configs, dict):
        raise ConfigError("configs must be a mapping", path=str(path))
    config_mode = configs.get("mode", "auto")
    return require_allowed(config_mode, ALLOWED_CONFIG_MODES, "configs.mode", path)


def parse_single_scope(name: str, value: object, path: Path) -> Scope:
    if not isinstance(value, dict):
        raise ConfigError(f"scope {name!r} must be a mapping", path=str(path))
    include_raw = value.get("include", []) or []
    if not isinstance(include_raw, list):
        raise ConfigError(f"scope {name!r} include must be a list", path=str(path))
    exclude_raw = value.get("exclude", []) or []
    if exclude_raw is None:
        exclude_raw = []
    if not isinstance(exclude_raw, list):
        raise ConfigError(f"scope {name!r} exclude must be a list", path=str(path))
    target_raw = value.get("target", ".")
    if not isinstance(target_raw, (str, Path)):
        raise ConfigError(f"scope {name!r} target must be a string", path=str(path))
    return Scope(
        target=Path(target_raw),
        include=tuple(str(i) for i in include_raw),
        exclude=tuple(str(e) for e in exclude_raw),
        respect_gitignore=bool(value.get("respect-gitignore", True)),
    )


def parse_scopes(raw: object, path: Path) -> dict[str, Scope] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError("scopes must be a mapping", path=str(path))
    return {str(name): parse_single_scope(str(name), value, path) for name, value in raw.items()}


def parse_allowlists(raw: object, path: Path) -> dict[str, str] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError("allowlists must be a mapping", path=str(path))
    return {str(key): parse_allowlist_binding(str(key), value, path) for key, value in raw.items()}


def parse_allowlist_binding(gate_id: str, value: object, path: Path) -> str:
    if isinstance(value, str):
        allowlist_path = value.strip()
        if not allowlist_path:
            raise ConfigError(
                f"allowlists[{gate_id!r}] requires a non-empty path",
                path=str(path),
            )
        return allowlist_path
    if isinstance(value, dict):
        raise ConfigError(
            f"allowlists[{gate_id!r}] must be an allowlist file path",
            hint=(
                "use gate-id: <allowlist-file>; document each exception with "
                "path and reason in that file"
            ),
            path=str(path),
        )
    raise ConfigError(
        f"allowlists[{gate_id!r}] must be an allowlist file path",
        path=str(path),
    )


def parse_config(raw: dict, path: Path) -> ProjectConfig:
    """Parse a raw config mapping without scope-source resolution."""
    return ProjectConfigLoader.parse_config_dict(
        raw,
        path,
        project_root=path.parent,
        pyproject_path=None,
    )
