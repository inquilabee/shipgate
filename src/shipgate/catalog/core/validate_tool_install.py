"""Install metadata validation for catalog tools."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.catalog.core.python_spec import PythonVersionSpec
from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition


def validate_tool_install(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None:
        return
    if install.manager not in ("python", "binary"):
        raise CatalogError(f"tool {tool.id!r} has unsupported install manager")
    validate_install_basename(tool, install.package, label="install.package")
    if install.binary:
        validate_install_basename(tool, install.binary, label="install.binary")
    validate_exact_pin(tool)
    validate_known_bad(tool)
    validate_download(tool)
    validate_requires_python(tool)


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
    validate_install_basename(
        tool, download.asset_template, label="install.download.asset_template"
    )
    validate_install_basename(tool, download.binary_name, label="install.download.binary_name")


def validate_requires_python(tool: ToolDefinition) -> None:
    install = tool.install
    if install is None or not install.requires_python:
        return
    try:
        PythonVersionSpec.parse(install.requires_python)
    except ValueError as exc:
        raise CatalogError(
            f"tool {tool.id!r} install.requires_python is invalid: {install.requires_python!r}"
        ) from exc


def validate_install_basename(tool: ToolDefinition, raw: str, *, label: str) -> None:
    candidate = Path(raw)
    if not raw or raw in {".", ".."} or candidate.name != raw or "/" in raw or "\\" in raw:
        raise CatalogError(f"tool {tool.id!r} {label} must be a basename, got {raw!r}")


def normalized_pin(version: str) -> str:
    raw = version.strip()
    cleaned = raw[2:].strip() if raw.startswith("==") else raw
    return cleaned.lstrip("v")
