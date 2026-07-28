"""Load and normalize [tool.shipgate] from pyproject.toml."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.core.toml_io import load_toml_mapping
from shipgate.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path


class ShipgateSectionNormalizer:
    SCOPE_KEY_ALIASES: ClassVar[dict[str, str]] = {
        "respect_gitignore": "respect-gitignore",
    }
    TOP_LEVEL_KEY_ALIASES: ClassVar[dict[str, str]] = {
        "error_format": "error-format",
        "error_formatters": "error-formatters",
        "auto_install": "auto-install",
        "fail_fast": "fail-fast",
        "changed_only": "changed-only",
    }

    def __init__(self, aliases: dict[str, str] | None = None) -> None:
        self._aliases = aliases or self.TOP_LEVEL_KEY_ALIASES

    def normalize_mapping(self, value: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            canonical = self._aliases.get(key, key)
            if canonical in normalized and canonical != key:
                continue
            if isinstance(item, dict):
                normalized[canonical] = (
                    self._normalize_scope_mapping(item) if canonical == "scopes" else dict(item)
                )
                continue
            normalized[canonical] = item
        return normalized

    def _normalize_scope_mapping(self, scopes: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for name, value in scopes.items():
            if not isinstance(value, dict):
                normalized[str(name)] = value
                continue
            scope_value: dict[str, Any] = {}
            for key, item in value.items():
                scope_value[self.SCOPE_KEY_ALIASES.get(key, key)] = item
            normalized[str(name)] = scope_value
        return normalized


class PyprojectPolicyLoader:
    """Read pyproject.toml and extract ShipGate policy tables."""

    @staticmethod
    def discover_path(project_root: Path) -> Path | None:
        candidate = project_root / "pyproject.toml"
        return candidate.resolve() if candidate.is_file() else None

    @staticmethod
    def load_shipgate_section(path: Path) -> dict[str, Any] | None:
        raw = load_toml_mapping(path, error_cls=ConfigError)
        tool = raw.get("tool")
        if not isinstance(tool, dict):
            return None
        shipgate = tool.get("shipgate")
        if shipgate is None:
            return None
        if not isinstance(shipgate, dict):
            raise ConfigError("[tool.shipgate] must be a table", path=str(path))
        return ShipgateSectionNormalizer().normalize_mapping(shipgate)

    @classmethod
    def load_section(cls, path: Path, dotted_path: str) -> dict[str, Any]:
        raw = load_toml_mapping(path, error_cls=ConfigError)
        return cls._section_at_path(raw, dotted_path)

    @staticmethod
    def _section_at_path(raw: dict[str, Any], dotted_path: str) -> dict[str, Any]:
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
