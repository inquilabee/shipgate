"""Install metadata validation for catalog tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition


def validate_tool_install(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None:
        return
    if install.manager not in ("python", "binary"):
        raise CatalogError(f"tool {tool.id!r} has unsupported install manager")
    validate_exact_pin(tool)
    validate_known_bad(tool)
    validate_download(tool)


def validate_exact_pin(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None:
        return
    version = install.version.strip()
    if not version:
        raise CatalogError(f"tool {tool.id!r} install.version must be an exact pin")
    if version.startswith((">=", "<=", ">", "<", "~=", "!=")) or version == "*":
        raise CatalogError(
            f"tool {tool.id!r} install.version must be an exact pin, got {version!r}"
        )


def validate_known_bad(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None:
        return
    pin = normalized_pin(install.version)
    bad = {normalized_pin(item) for item in install.known_bad}
    if pin in bad:
        raise CatalogError(
            f"tool {tool.id!r} install.version {install.version!r} is listed in known_bad"
        )


def validate_download(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None or install.download is None:
        return
    download = install.download
    if not download.repo.strip():
        raise CatalogError(f"tool {tool.id!r} install.download.repo is required")
    if not download.asset_template.strip():
        raise CatalogError(f"tool {tool.id!r} install.download.asset_template is required")
    if not download.binary_name.strip():
        raise CatalogError(f"tool {tool.id!r} install.download.binary_name is required")


def normalized_pin(version: str) -> str:
    raw = version.strip()
    cleaned = raw[2:].strip() if raw.startswith("==") else raw
    return cleaned.lstrip("v")
