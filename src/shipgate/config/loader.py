"""Project config loader."""

from __future__ import annotations

from pathlib import Path

from shipgate.config.discovery import discover_config_path
from shipgate.config.schema import (
    ALLOWED_CONFIG_MODES,
    ALLOWED_ENV_VALUES,
    ALLOWED_ERROR_FORMATS,
    ALLOWED_TOP_LEVEL_KEYS,
)
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.domain.project import CheckBinding, ProjectConfig, Scope
from shipgate.errors import ConfigError
from shipgate.paths import find_project_root


def load_config(
    *,
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> ProjectConfig:
    root = (project_root or find_project_root()).resolve()
    path = discover_config_path(root, config_path)
    if path is None:
        return ProjectConfig()
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}", path=str(path))
    raw = load_yaml_mapping(path, error_cls=ConfigError)
    if not raw:
        return ProjectConfig()
    return parse_config(raw, path)


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


def parse_config(raw: dict, path: Path) -> ProjectConfig:
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
    scopes = parse_scopes(raw.get("scopes"), path)
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
    )
