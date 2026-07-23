"""Resolve ShipGate scope ``source`` references."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.errors import ConfigError

from .pyproject import PyprojectPolicyLoader

if TYPE_CHECKING:
    from pathlib import Path


class ScopeSourceResolver:
    """Expand scope ``source`` refs from pyproject tool sections or gate configs."""

    def __init__(
        self,
        *,
        project_root: Path,
        pyproject_path: Path | None,
        config_path: Path,
    ) -> None:
        self._project_root = project_root
        self._pyproject_path = pyproject_path
        self._config_path = config_path

    def resolve(self, raw_scopes: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for name, value in raw_scopes.items():
            if not isinstance(value, dict):
                resolved[str(name)] = value
                continue
            if "source" not in value:
                resolved[str(name)] = value
                continue
            source = value.get("source")
            if not isinstance(source, str) or not source:
                raise ConfigError(
                    f"scope {name!r} source must be a non-empty string",
                    path=str(self._config_path),
                )
            include, exclude = self._resolve_source(source, scope_name=str(name))
            merged = dict(value)
            del merged["source"]
            if "include" not in merged:
                merged["include"] = list(include)
            if "exclude" not in merged:
                merged["exclude"] = list(exclude)
            resolved[str(name)] = merged
        return resolved

    def _resolve_source(
        self,
        source: str,
        *,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        if source.startswith("gate:"):
            return self._resolve_gate_source(source.removeprefix("gate:"), scope_name=scope_name)
        if source.startswith("tool."):
            return self._resolve_tool_source(source, scope_name=scope_name)
        raise ConfigError(
            f"scope {scope_name!r} has unsupported source {source!r}; "
            "use tool.<section> or gate:<gate-id>",
            path=str(self._config_path),
        )

    def _resolve_tool_source(
        self,
        source: str,
        *,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        path = self._pyproject_path or PyprojectPolicyLoader.discover_path(self._project_root)
        if path is None:
            raise ConfigError(
                f"scope {scope_name!r} source {source!r} requires pyproject.toml",
                path=str(self._config_path),
            )
        try:
            section = PyprojectPolicyLoader.load_section(path, source)
        except KeyError as exc:
            raise ConfigError(
                f"scope {scope_name!r} source {source!r} not found in {path.name}",
                path=str(self._config_path),
            ) from exc
        except TypeError as exc:
            raise ConfigError(str(exc), path=str(self._config_path)) from exc
        return self._paths_from_section(section, scope_name=scope_name)

    def _resolve_gate_source(
        self,
        gate_id: str,
        *,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        gate_name = gate_id if gate_id.startswith("gate.") else f"gate.{gate_id}"
        gate_path = self._project_root / ".shipgate" / "configs" / "gates" / f"{gate_name}.yaml"
        if not gate_path.is_file():
            raise ConfigError(
                f"scope {scope_name!r} gate source not found: {gate_path}",
                path=str(self._config_path),
            )
        raw = load_yaml_mapping(gate_path, error_cls=ConfigError)
        scan_roots = raw.get("scan_roots", ["."])
        if not isinstance(scan_roots, list):
            raise ConfigError(
                f"scope {scope_name!r} gate source {gate_name!r} scan_roots must be a list",
                path=str(self._config_path),
            )
        return tuple(str(item) for item in scan_roots), ()

    def _paths_from_section(
        self,
        section: dict[str, Any],
        *,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        include_raw = section.get("include", [])
        exclude_raw = section.get("exclude", [])
        if include_raw is None:
            include_raw = []
        if exclude_raw is None:
            exclude_raw = []
        if not isinstance(include_raw, list):
            raise ConfigError(
                f"scope {scope_name!r} source include must be a list",
                path=str(self._config_path),
            )
        if not isinstance(exclude_raw, list):
            raise ConfigError(
                f"scope {scope_name!r} source exclude must be a list",
                path=str(self._config_path),
            )
        return tuple(str(item) for item in include_raw), tuple(str(item) for item in exclude_raw)
