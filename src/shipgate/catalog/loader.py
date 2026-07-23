"""Bundled catalog loader."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.catalog.core import CatalogParser, CatalogValidator, ToolExtendsResolver
from shipgate.core.yaml_io import load_yaml_mapping
from shipgate.errors import CatalogError
from shipgate.paths import PROJECT_CATALOG_DIR

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog


class CatalogLoader:
    """Load bundled and project catalog YAML into a raw dict for parsing.

    Merges project overlays, resolves tool inheritance, and orchestrates parse and validate.
    """

    def __init__(
        self,
        path: Path | None = None,
        project_root: Path | None = None,
    ) -> None:
        self._path = path
        self._project_root = project_root
        self._bundled_root: Path | None = None

    @classmethod
    def load(cls, path: Path | None = None, *, project_root: Path | None = None) -> Catalog:
        return cls(path, project_root)._load()

    @classmethod
    def merge(cls, base: dict, overlay: dict) -> dict:
        return cls()._merge_raw(base, overlay)

    def _load(self) -> Catalog:
        raw = self._load_raw()
        catalog = CatalogParser.parse(raw)
        CatalogValidator.validate(catalog, self._bundled_root)
        return catalog

    def _load_raw(self) -> dict:
        if self._path is None:
            bundled = resources.files("shipgate.catalog.bundled")
            self._bundled_root = Path(str(bundled))
            bundled_raw = self._load_bundled_raw(bundled)
            bundled_tools = bundled_raw.get("tools", {}) or {}
            project_tools: dict = {}
            if self._project_root is not None:
                project_raw = self._load_project_raw(self._project_root)
                if project_raw:
                    project_tools = project_raw.get("tools", {}) or {}
                    raw = self._merge_raw(bundled_raw, project_raw)
                else:
                    raw = bundled_raw
            else:
                raw = bundled_raw
            raw["tools"] = ToolExtendsResolver.resolve(bundled_tools, project_tools)
        else:
            raw = load_yaml_mapping(
                self._path,
                error_cls=CatalogError,
                invalid_message="invalid catalog YAML",
            )
            self._bundled_root = self._path.parent
            raw["tools"] = ToolExtendsResolver.resolve(raw.get("tools", {}) or {}, {})
        if not isinstance(raw, dict):
            raise CatalogError("catalog must be a mapping")
        return raw

    def _merge_raw(self, base: dict, overlay: dict) -> dict:
        """Merge project catalog overlay onto bundled raw catalog data."""
        merged = dict(base)
        for section in ("tools", "suites", "workflows", "capabilities"):
            overlay_section = overlay.get(section)
            if not overlay_section:
                continue
            base_section = dict(merged.get(section, {}))
            base_section.update(overlay_section)
            merged[section] = base_section
        return merged

    def _load_project_raw(self, project_root: Path) -> dict | None:
        """Load raw catalog data from `.shipgate/catalog/` when present."""
        catalog_dir = project_root / PROJECT_CATALOG_DIR
        if not catalog_dir.is_dir():
            return None
        raw: dict = {}
        tools_dir = catalog_dir / "tools"
        if tools_dir.is_dir():
            raw["tools"] = self._load_tools_dir(tools_dir)
        for section in ("suites", "workflows", "capabilities"):
            section_path = catalog_dir / f"{section}.yaml"
            if section_path.is_file():
                raw[section] = self._load_section(catalog_dir, section)
        return raw or None

    def _load_bundled_raw(self, bundled: object) -> dict:
        """Load split catalog from bundled/catalog/ directory."""
        bundled_root = Path(str(bundled))
        catalog_dir = bundled_root / "catalog"
        raw: dict = {"tools": self._load_tools_dir(catalog_dir / "tools")}
        for section in ("suites", "workflows", "capabilities"):
            raw[section] = self._load_section(catalog_dir, section)
        return raw

    def _load_tools_dir(self, tools_dir: Path) -> dict:
        tools: dict = {}
        for tool_path in sorted(tools_dir.iterdir()):
            if tool_path.suffix != ".yaml":
                continue
            tool_id, tool_data = self._load_tool_file(tool_path)
            tools[tool_id] = tool_data
        return tools

    def _load_tool_file(self, tool_path: Path) -> tuple[str, dict]:
        tool_raw = load_yaml_mapping(
            tool_path,
            error_cls=CatalogError,
            invalid_message=f"invalid catalog YAML: {tool_path.name}",
        )
        if not isinstance(tool_raw, dict):
            raise CatalogError(f"tool file must be a mapping: {tool_path.name}")
        expected_id = tool_path.stem
        if len(tool_raw) != 1 or expected_id not in tool_raw:
            raise CatalogError(
                f"tool file {tool_path.name!r} must contain exactly one key {expected_id!r}"
            )
        return expected_id, tool_raw[expected_id]

    def _load_section(self, catalog_dir: Path, section: str) -> dict:
        section_path = catalog_dir / f"{section}.yaml"
        section_raw = load_yaml_mapping(
            section_path,
            error_cls=CatalogError,
            invalid_message=f"invalid catalog YAML: {section_path.name}",
        )
        if not isinstance(section_raw, dict) or section not in section_raw:
            raise CatalogError(f"expected top-level {section!r} key in {section_path.name}")
        return section_raw[section]
