"""Load and normalize [tool.shipgate] from pyproject.toml."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Any

from shipgate.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path

SCOPE_KEY_ALIASES = {
    "respect_gitignore": "respect-gitignore",
}

TOP_LEVEL_KEY_ALIASES = {
    "error_format": "error-format",
    "error_formatters": "error-formatters",
    "auto_install": "auto-install",
    "fail_fast": "fail-fast",
    "changed_only": "changed-only",
}


def load_pyproject_toml(path: Path) -> dict[str, Any]:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML: {exc}", path=str(path)) from exc
    if not isinstance(raw, dict):
        raise ConfigError("pyproject.toml must be a mapping", path=str(path))
    return raw


def discover_pyproject_path(project_root: Path) -> Path | None:
    candidate = project_root / "pyproject.toml"
    if candidate.is_file():
        return candidate.resolve()
    return None


def load_shipgate_section(path: Path) -> dict[str, Any] | None:
    raw = load_pyproject_toml(path)
    tool = raw.get("tool")
    if not isinstance(tool, dict):
        return None
    shipgate = tool.get("shipgate")
    if shipgate is None:
        return None
    if not isinstance(shipgate, dict):
        raise ConfigError("[tool.shipgate] must be a table", path=str(path))
    return normalize_shipgate_section(shipgate)


def normalize_shipgate_section(section: dict[str, Any]) -> dict[str, Any]:
    return ShipgateSectionNormalizer.normalize_mapping(section, aliases=TOP_LEVEL_KEY_ALIASES)


class ShipgateSectionNormalizer:
    @staticmethod
    def normalize_mapping(
        value: dict[str, Any],
        *,
        aliases: dict[str, str],
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            canonical = aliases.get(key, key)
            if canonical in normalized and canonical != key:
                continue
            if isinstance(item, dict):
                if canonical == "scopes":
                    normalized[canonical] = ShipgateSectionNormalizer.normalize_scope_mapping(
                        item,
                        SCOPE_KEY_ALIASES,
                    )
                else:
                    normalized[canonical] = dict(item)
                continue
            normalized[canonical] = item
        return normalized

    @staticmethod
    def normalize_scope_mapping(
        scopes: dict[str, Any],
        aliases: dict[str, str],
    ) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for name, value in scopes.items():
            if not isinstance(value, dict):
                normalized[str(name)] = value
                continue
            scope_value: dict[str, Any] = {}
            for key, item in value.items():
                scope_value[aliases.get(key, key)] = item
            normalized[str(name)] = scope_value
        return normalized


def section_at_path(raw: dict[str, Any], dotted_path: str) -> dict[str, Any]:
    node: Any = raw
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            msg = f"pyproject section not found: {dotted_path!r}"
            raise KeyError(msg)
        node = node[part]
    if not isinstance(node, dict):
        msg = f"pyproject section must be a table: {dotted_path!r}"
        raise TypeError(msg)
    return node
