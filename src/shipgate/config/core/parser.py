"""Project config YAML dict → domain object parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

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
                bindings.append(self._parse_check_binding(str(runnable), value))
            return (), tuple(bindings)
        raise ConfigError("checks must be a list or mapping", path=str(self._path))

    def _parse_check_binding(self, runnable_id: str, value: object) -> CheckBinding:
        scope_name = None
        threshold = None
        average_mode = None
        average_threshold = None
        median_mode = None
        median_threshold = None
        minimum_mode = None
        minimum_threshold = None
        maximum_mode = None
        maximum_threshold = None
        p95_mode = None
        p95_threshold = None
        if isinstance(value, dict):
            binding: dict[str, Any] = cast("dict[str, Any]", value)
            scope_name = binding.get("scope")
            if scope_name is not None:
                scope_name = str(scope_name)
            threshold_raw = binding.get("threshold")
            if threshold_raw is not None:
                threshold = str(threshold_raw)
            average_mode, average_threshold = self._parse_metric_gate(
                runnable_id,
                binding,
                field="average",
            )
            median_mode, median_threshold = self._parse_metric_gate(
                runnable_id,
                binding,
                field="median",
            )
            minimum_mode, minimum_threshold = self._parse_metric_gate(
                runnable_id,
                binding,
                field="minimum",
            )
            maximum_mode, maximum_threshold = self._parse_metric_gate(
                runnable_id,
                binding,
                field="maximum",
            )
            p95_mode, p95_threshold = self._parse_metric_gate(
                runnable_id,
                binding,
                field="p95",
            )
        return CheckBinding(
            runnable=runnable_id,
            scope=scope_name,
            threshold=threshold,
            average_mode=average_mode,
            average_threshold=average_threshold,
            median_mode=median_mode,
            median_threshold=median_threshold,
            minimum_mode=minimum_mode,
            minimum_threshold=minimum_threshold,
            maximum_mode=maximum_mode,
            maximum_threshold=maximum_threshold,
            p95_mode=p95_mode,
            p95_threshold=p95_threshold,
        )

    def _parse_metric_gate(
        self,
        runnable_id: str,
        value: dict[str, Any],
        *,
        field: str,
    ) -> tuple[str | None, float | None]:
        mode = self._parse_metric_mode(runnable_id, value, field=field)
        bound = self._parse_metric_threshold(runnable_id, value, field=field)
        if mode == "threshold" and bound is None:
            raise ConfigError(
                f"checks.{runnable_id}: {field}-mode threshold requires {field}-threshold",
                path=str(self._path),
            )
        return mode, bound

    def _parse_metric_mode(
        self,
        runnable_id: str,
        value: dict[str, Any],
        *,
        field: str,
    ) -> str | None:
        raw = value.get(f"{field}-mode", value.get(f"{field}_mode"))
        if raw is None:
            return None
        mode = str(raw).strip().lower()
        if mode not in {"threshold", "progressive"}:
            raise ConfigError(
                f"checks.{runnable_id}: invalid {field}-mode {raw!r}",
                path=str(self._path),
            )
        return mode

    def _parse_metric_threshold(
        self,
        runnable_id: str,
        value: dict[str, Any],
        *,
        field: str,
    ) -> float | None:
        raw = value.get(f"{field}-threshold", value.get(f"{field}_threshold"))
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                f"checks.{runnable_id}: {field}-threshold must be a number",
                path=str(self._path),
            ) from exc

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
                    self._allowlist_message(gate_id, "requires a non-empty path"),
                    path=str(self._path),
                )
            return allowlist_path
        if isinstance(value, dict):
            raise ConfigError(
                self._allowlist_message(gate_id, "must be an allowlist file path"),
                hint=(
                    "use gate-id: <allowlist-file>; document each exception with "
                    "path and reason in that file"
                ),
                path=str(self._path),
            )
        raise ConfigError(
            self._allowlist_message(gate_id, "must be an allowlist file path"),
            path=str(self._path),
        )

    @staticmethod
    def _allowlist_message(gate_id: str, detail: str) -> str:
        return f"allowlists[{gate_id!r}] {detail}"
