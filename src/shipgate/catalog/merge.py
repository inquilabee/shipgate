"""Merge external catalog packs into bundled catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from shipgate.domain.catalog import Catalog, SuiteDefinition, ToolDefinition, WorkflowDefinition
from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from pathlib import Path


def merge_catalogs(base: Catalog, *extensions: Catalog) -> Catalog:
    tools: dict[str, ToolDefinition] = dict(base.tools)
    suites: dict[str, SuiteDefinition] = dict(base.suites)
    workflows: dict[str, WorkflowDefinition] = dict(base.workflows)
    capabilities: dict[str, tuple[str, ...]] = dict(base.capabilities)
    for ext in extensions:
        tools.update(ext.tools)
        suites.update(ext.suites)
        workflows.update(ext.workflows)
        capabilities.update(ext.capabilities)
    return Catalog(
        tools=tools,
        suites=suites,
        workflows=workflows,
        capabilities=capabilities,
    )


def load_catalog_pack(path: Path) -> Catalog:
    if not path.is_file():
        raise CatalogError(f"catalog pack not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CatalogError(f"invalid catalog pack YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise CatalogError("catalog pack must be a mapping")
    from shipgate.catalog.loader import parse_catalog

    return parse_catalog(raw)
