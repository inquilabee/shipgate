"""Project config loader."""

from __future__ import annotations

from pathlib import Path

import yaml

from shipgate.config.discovery import discover_config_path
from shipgate.config.schema import (
    ALLOWED_CONFIG_MODES,
    ALLOWED_ENV_VALUES,
    ALLOWED_ERROR_FORMATS,
    ALLOWED_TOP_LEVEL_KEYS,
)
from shipgate.domain.project import ProjectConfig, Scope
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
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML: {exc}", path=str(path)) from exc
    if raw is None:
        return ProjectConfig()
    if not isinstance(raw, dict):
        raise ConfigError("config must be a mapping", path=str(path))
    return _parse_config(raw, path)


def _parse_config(raw: dict, path: Path) -> ProjectConfig:
    unknown = set(raw) - ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        raise ConfigError(
            f"unknown config key(s): {', '.join(sorted(unknown))}",
            path=str(path),
        )

    env = raw.get("env", "managed")
    if env not in ALLOWED_ENV_VALUES:
        raise ConfigError(f"invalid env: {env!r}", path=str(path))

    error_format = raw.get("error-format", "json")
    if error_format not in ALLOWED_ERROR_FORMATS:
        raise ConfigError(f"invalid error-format: {error_format!r}", path=str(path))

    configs = raw.get("configs", {}) or {}
    if not isinstance(configs, dict):
        raise ConfigError("configs must be a mapping", path=str(path))
    config_mode = configs.get("mode", "auto")
    if config_mode not in ALLOWED_CONFIG_MODES:
        raise ConfigError(f"invalid configs.mode: {config_mode!r}", path=str(path))

    checks_raw = raw.get("checks", []) or []
    if not isinstance(checks_raw, list):
        raise ConfigError("checks must be a list", path=str(path))
    checks = tuple(str(c) for c in checks_raw)

    scopes = _parse_scopes(raw.get("scopes"), path)

    target = Path(raw.get("target", "."))
    suite = raw.get("suite", "standard")
    if suite is not None:
        suite = str(suite)

    return ProjectConfig(
        suite=suite,
        env=env,
        target=target,
        error_format=error_format,
        config_mode=config_mode,
        checks=checks,
        scopes=scopes,
        auto_install=bool(raw.get("auto-install", False)),
        parallel=bool(raw.get("parallel", False)),
        fail_fast=bool(raw.get("fail-fast", False)),
    )


def _parse_scopes(raw: object, path: Path) -> dict[str, Scope] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ConfigError("scopes must be a mapping", path=str(path))
    scopes: dict[str, Scope] = {}
    for name, value in raw.items():
        if not isinstance(value, dict):
            raise ConfigError(f"scope {name!r} must be a mapping", path=str(path))
        include = tuple(str(i) for i in value.get("include", []) or [])
        exclude = tuple(str(e) for e in value.get("exclude", []) or [])
        scopes[str(name)] = Scope(
            target=Path(value.get("target", ".")),
            include=include,
            exclude=exclude,
            respect_gitignore=bool(value.get("respect-gitignore", True)),
        )
    return scopes
