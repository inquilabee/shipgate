"""Project config YAML dict → domain object parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shipgate.config.schema import (
    ALLOWED_CONFIG_MODES,
    ALLOWED_ENV_VALUES,
    ALLOWED_ERROR_FORMATS,
    ALLOWED_TOP_LEVEL_KEYS,
)
from shipgate.domain.project import CheckBinding, ProjectConfig, Scope
from shipgate.errors import ConfigError


class ProjectConfigParser:
    """Transform raw project config dicts into frozen ``ProjectConfig`` domain objects.

    Expects scope ``source`` refs to be resolved before parsing; performs schema checks only.
    """

    def __init__(self, raw: dict[str, Any], path: Path) -> None:
        self._raw = raw
        self._path = path

    @classmethod
    def parse(cls, raw: dict[str, Any], path: Path) -> ProjectConfig:
        return cls(raw, path)._parse()

    def _parse(self) -> ProjectConfig:
        self._validate_top_level_keys()
        env = self._require_allowed(
            self._raw.get("env", "managed"),
            ALLOWED_ENV_VALUES,
            "env",
        )
        error_format_raw = self._raw.get("error-format")
        error_format = None
        if error_format_raw is not None:
            error_format = self._require_allowed(
                error_format_raw,
                ALLOWED_ERROR_FORMATS,
                "error-format",
            )
        config_mode = self._parse_config_mode()
        checks, check_bindings = self._parse_checks()
        scopes = self._parse_scopes(self._raw.get("scopes"))
        allowlists = self._parse_allowlists(self._raw.get("allowlists"))
        suite = self._raw.get("suite", "standard")
        if suite is not None:
            suite = str(suite)
        return ProjectConfig(
            suite=suite,
            env=env,
            target=Path(self._raw.get("target", ".")),
            error_format=error_format,
            config_mode=config_mode,
            checks=checks,
            check_bindings=check_bindings,
            scopes=scopes,
            auto_install=bool(self._raw.get("auto-install", False)),
            parallel=bool(self._raw.get("parallel", False)),
            fail_fast=bool(self._raw.get("fail-fast", False)),
            changed_only=bool(self._raw.get("changed-only", False)),
            since=str(self._raw["since"]) if self._raw.get("since") is not None else None,
            allowlists=allowlists,
        )

    def _validate_top_level_keys(self) -> None:
        unknown = set(self._raw) - ALLOWED_TOP_LEVEL_KEYS
        if unknown:
            raise ConfigError(
                f"unknown config key(s): {', '.join(sorted(unknown))}",
                path=str(self._path),
            )

    def _require_allowed(
        self,
        value: object,
        allowed: set[str] | frozenset[str],
        label: str,
    ) -> str:
        if value not in allowed:
            raise ConfigError(f"invalid {label}: {value!r}", path=str(self._path))
        return str(value)

    def _parse_checks(self) -> tuple[tuple[str, ...], tuple[CheckBinding, ...]]:
        checks_raw = self._raw.get("checks", []) or []
        if isinstance(checks_raw, list):
            return tuple(str(check_id) for check_id in checks_raw), ()
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
        raise ConfigError("checks must be a list or mapping", path=str(self._path))

    def _parse_config_mode(self) -> str:
        configs = self._raw.get("configs", {}) or {}
        if not isinstance(configs, dict):
            raise ConfigError("configs must be a mapping", path=str(self._path))
        config_mode = configs.get("mode", "auto")
        return self._require_allowed(config_mode, ALLOWED_CONFIG_MODES, "configs.mode")

    def _parse_single_scope(self, name: str, value: object) -> Scope:
        if not isinstance(value, dict):
            raise ConfigError(f"scope {name!r} must be a mapping", path=str(self._path))
        include_raw = value.get("include", []) or []
        if not isinstance(include_raw, list):
            raise ConfigError(f"scope {name!r} include must be a list", path=str(self._path))
        exclude_raw = value.get("exclude", []) or []
        if exclude_raw is None:
            exclude_raw = []
        if not isinstance(exclude_raw, list):
            raise ConfigError(f"scope {name!r} exclude must be a list", path=str(self._path))
        target_raw = value.get("target", ".")
        if not isinstance(target_raw, (str, Path)):
            raise ConfigError(f"scope {name!r} target must be a string", path=str(self._path))
        return Scope(
            target=Path(target_raw),
            include=tuple(str(item) for item in include_raw),
            exclude=tuple(str(item) for item in exclude_raw),
            respect_gitignore=bool(value.get("respect-gitignore", True)),
        )

    def _parse_scopes(self, raw: object) -> dict[str, Scope] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise ConfigError("scopes must be a mapping", path=str(self._path))
        return {
            str(name): self._parse_single_scope(str(name), value) for name, value in raw.items()
        }

    def _parse_allowlists(self, raw: object) -> dict[str, str] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise ConfigError("allowlists must be a mapping", path=str(self._path))
        return {
            str(key): self._parse_allowlist_binding(str(key), value) for key, value in raw.items()
        }

    def _parse_allowlist_binding(self, gate_id: str, value: object) -> str:
        if isinstance(value, str):
            allowlist_path = value.strip()
            if not allowlist_path:
                raise ConfigError(
                    f"allowlists[{gate_id!r}] requires a non-empty path",
                    path=str(self._path),
                )
            return allowlist_path
        if isinstance(value, dict):
            raise ConfigError(
                f"allowlists[{gate_id!r}] must be an allowlist file path",
                hint=(
                    "use gate-id: <allowlist-file>; document each exception with "
                    "path and reason in that file"
                ),
                path=str(self._path),
            )
        raise ConfigError(
            f"allowlists[{gate_id!r}] must be an allowlist file path",
            path=str(self._path),
        )
