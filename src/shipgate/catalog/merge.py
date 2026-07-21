"""Merge external catalog packs into bundled catalog."""

from __future__ import annotations

from pathlib import Path

import yaml

from shipgate.domain.catalog import Catalog, SuiteDefinition, ToolDefinition
from shipgate.errors import CatalogError


def merge_catalogs(base: Catalog, *extensions: Catalog) -> Catalog:
    tools: dict[str, ToolDefinition] = dict(base.tools)
    suites: dict[str, SuiteDefinition] = dict(base.suites)
    for ext in extensions:
        for tool_id, tool in ext.tools.items():
            if tool_id in tools:
                tools[tool_id] = tool
            else:
                tools[tool_id] = tool
        for suite_id, suite in ext.suites.items():
            suites[suite_id] = suite
    return Catalog(tools=tools, suites=suites)


def load_catalog_pack(path: Path, parse_fn=None) -> Catalog:
    if not path.is_file():
        raise CatalogError(f"catalog pack not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogError(f"invalid catalog pack YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise CatalogError("catalog pack must be a mapping")
    from shipgate.catalog.loader import _parse_catalog

    return _parse_catalog(raw)
