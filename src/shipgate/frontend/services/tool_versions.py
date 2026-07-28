"""Resolve installed or catalog versions for the Tool docs page."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_PYTHON_ENV
from shipgate.runtime.environment import resolve_executable, system_environment

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition

VERSION_ATTEMPTS = ("--version", "-version", "-V", "version")
TIMEOUT_S = 3.0
LEADING_NAME = re.compile(r"^[A-Za-z0-9._-]+\s+")
VERSION_LINE = re.compile(
    r"(?:^|\b)version[:\s,]+[vV]?(?P<version>\d+\.\d+(?:\.\d+)?(?:[.\w-]*)?)",
    re.IGNORECASE,
)
SEMVER = re.compile(r"\d+\.\d+(?:\.\d+)?(?:[.\w-]*)?")
PACKAGE_NAME = re.compile(r"^([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class ToolDocsRow:
    id: str
    name: str
    description: str
    documentation_url: str | None
    version: str
    tags: tuple[str, ...] = ()


def tool_docs_rows(catalog: Catalog, primary_root: Path) -> list[ToolDocsRow]:
    return [
        ToolDocsRow(
            id=tool_id,
            name=tool.display_name or tool_id,
            description=tool.description or tool_id,
            documentation_url=tool.documentation_url,
            version=resolve_version(tool, primary_root),
            tags=tuple(tool.tags),
        )
        for tool_id, tool in sorted(catalog.tools.items())
    ]


def resolve_version(tool: ToolDefinition, primary_root: Path) -> str:
    if installed := installed_version(tool, primary_root):
        return installed
    return (
        pip_version
        if (pip_version := pip_show_version(tool, primary_root))
        else (tool.install.version if tool.install and tool.install.version else "—")
    )


def installed_version(tool: ToolDefinition, primary_root: Path) -> str | None:
    try:
        binary = resolve_executable(
            tool.executable,
            system_environment(),
            install_binary=tool.install.binary if tool.install else None,
        )
    except InstallError:
        try:
            from shipgate.runtime.environment import managed_environment

            binary = resolve_executable(
                tool.executable,
                managed_environment(primary_root),
                install_binary=tool.install.binary if tool.install else None,
            )
        except InstallError:
            return None
    for flag in VERSION_ATTEMPTS:
        if parsed := run_version_command(binary, flag, tool.executable):
            return parsed
    return None


def run_version_command(binary: str, flag: str, binary_name: str) -> str | None:
    command = [binary, flag]
    try:
        completed = run_command(command, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    return parse_version_from_output(text, binary_name) if text else None


def parse_version_from_output(text: str, binary_name: str) -> str | None:
    for line in text.splitlines():
        if version := version_from_line(line.strip(), binary_name):
            return version
    return semver_fallback(text, binary_name)


def version_from_line(stripped: str, binary_name: str) -> str | None:
    if not stripped:
        return None
    if match := VERSION_LINE.search(stripped):
        return clean_version(match["version"])
    normalized = normalize_version_line(stripped, binary_name)
    if not is_plausible_version(normalized, binary_name):
        return None
    found = SEMVER.search(normalized)
    return clean_version(found[0]) if found else None


def semver_fallback(text: str, binary_name: str) -> str | None:
    found = SEMVER.search(text)
    return (
        clean_version(found[0]) if found and is_plausible_version(found[0], binary_name) else None
    )


def pip_show_version(tool: ToolDefinition, primary_root: Path) -> str | None:
    if tool.install is None or tool.install.manager != "python":
        return None
    resolved_package = package_name(tool.install.package)
    if resolved_package is None:
        return None
    python = (primary_root / PROJECT_MANAGED_PYTHON_ENV) / "bin" / "python"
    if not python.is_file():
        return None
    try:
        completed = run_command(
            [str(python), "-m", "pip", "show", resolved_package],
            timeout=TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    for line in completed.stdout.splitlines():
        if line.lower().startswith("version:"):
            return line.split(":", 1)[1].strip() or None
    return None


def package_name(package: str | None) -> str | None:
    if not package:
        return None
    match = PACKAGE_NAME.match(package.strip())
    return match[1] if match else None


def normalize_version_line(line: str, binary_name: str) -> str:
    lowered = line.lower()
    prefix = binary_name.lower()
    return (
        line.removeprefix(binary_name).strip()
        if lowered.startswith(prefix + " ")
        else (
            line[len(binary_name) + 1 :].strip()
            if lowered.startswith(prefix + "/")
            else LEADING_NAME.sub("", line, count=1).strip() or line
        )
    )


def clean_version(value: str) -> str:
    return value.lstrip("vV")


def is_plausible_version(value: str, binary_name: str) -> bool:
    return (
        False
        if not value or value.lower() == binary_name.lower()
        else SEMVER.search(value) is not None
    )
