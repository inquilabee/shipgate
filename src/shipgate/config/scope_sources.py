"""Resolve ShipGate scope `source` references."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shipgate.config.pyproject import discover_pyproject_path, load_pyproject_toml, section_at_path
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path


def resolve_scope_sources(
    raw_scopes: dict[str, Any],
    *,
    project_root: Path,
    pyproject_path: Path | None,
    config_path: Path,
) -> dict[str, Any]:
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
                path=str(config_path),
            )
        include, exclude = resolve_scope_source(
            source,
            project_root=project_root,
            pyproject_path=pyproject_path,
            config_path=config_path,
            scope_name=str(name),
        )
        merged = dict(value)
        del merged["source"]
        if "include" not in merged:
            merged["include"] = list(include)
        if "exclude" not in merged:
            merged["exclude"] = list(exclude)
        resolved[str(name)] = merged
    return resolved


def resolve_scope_source(
    source: str,
    *,
    project_root: Path,
    pyproject_path: Path | None,
    config_path: Path,
    scope_name: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if source.startswith("gate:"):
        return ScopeSourceResolver.resolve_gate_source(
            source.removeprefix("gate:"),
            project_root=project_root,
            config_path=config_path,
            scope_name=scope_name,
        )
    if source.startswith("tool."):
        return ScopeSourceResolver.resolve_tool_source(
            source,
            project_root=project_root,
            pyproject_path=pyproject_path,
            config_path=config_path,
            scope_name=scope_name,
        )
    raise ConfigError(
        f"scope {scope_name!r} has unsupported source {source!r}; "
        "use tool.<section> or gate:<gate-id>",
        path=str(config_path),
    )


class ScopeSourceResolver:
    @staticmethod
    def resolve_tool_source(
        source: str,
        *,
        project_root: Path,
        pyproject_path: Path | None,
        config_path: Path,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        path = pyproject_path or discover_pyproject_path(project_root)
        if path is None:
            raise ConfigError(
                f"scope {scope_name!r} source {source!r} requires pyproject.toml",
                path=str(config_path),
            )
        try:
            section = section_at_path(load_pyproject_toml(path), source)
        except KeyError as exc:
            raise ConfigError(
                f"scope {scope_name!r} source {source!r} not found in {path.name}",
                path=str(config_path),
            ) from exc
        except TypeError as exc:
            raise ConfigError(str(exc), path=str(config_path)) from exc
        return ScopeSourceResolver.paths_from_section(
            section,
            config_path=config_path,
            scope_name=scope_name,
        )

    @staticmethod
    def resolve_gate_source(
        gate_id: str,
        *,
        project_root: Path,
        config_path: Path,
        scope_name: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        gate_name = gate_id if gate_id.startswith("gate.") else f"gate.{gate_id}"
        gate_path = project_root / ".shipgate" / "configs" / "gates" / f"{gate_name}.yaml"
        if not gate_path.is_file():
            raise ConfigError(
                f"scope {scope_name!r} gate source not found: {gate_path}",
                path=str(config_path),
            )
        raw = load_yaml_mapping(gate_path, error_cls=ConfigError)
        scan_roots = raw.get("scan_roots", ["."])
        if not isinstance(scan_roots, list):
            raise ConfigError(
                f"scope {scope_name!r} gate source {gate_name!r} scan_roots must be a list",
                path=str(config_path),
            )
        return tuple(str(item) for item in scan_roots), ()

    @staticmethod
    def paths_from_section(
        section: dict[str, Any],
        *,
        config_path: Path,
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
                path=str(config_path),
            )
        if not isinstance(exclude_raw, list):
            raise ConfigError(
                f"scope {scope_name!r} source exclude must be a list",
                path=str(config_path),
            )
        return tuple(str(item) for item in include_raw), tuple(str(item) for item in exclude_raw)
