"""Optional refactor enable config (``.shipgate/refactor.yaml`` / ``[tool.refactor]``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from refactor.inventory import parse_enable_tokens

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

REFACTOR_YAML_NAME = "refactor.yaml"


def load_enable_from_project(project_root: Path | None) -> frozenset[str]:
    if project_root is None:
        return frozenset()
    root = project_root.resolve()
    return frozenset(
        load_enable_from_shipgate_yaml(root) | load_enable_from_pyproject(root),
    )


def load_enable_from_shipgate_yaml(root: Path) -> frozenset[str]:
    path = root / ".shipgate" / REFACTOR_YAML_NAME
    if not path.is_file():
        return frozenset()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return enable_from_mapping(raw)


def load_enable_from_pyproject(root: Path) -> frozenset[str]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return frozenset()
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        return frozenset()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    tool = data.get("tool")
    return enable_from_mapping(tool.get("refactor")) if isinstance(tool, dict) else frozenset()


def enable_from_mapping(raw: object) -> frozenset[str]:
    if not isinstance(raw, dict):
        return frozenset()
    enable = raw.get("enable")
    return (
        frozenset()
        if enable is None
        else (
            parse_enable_tokens([enable])
            if isinstance(enable, str)
            else (
                parse_enable_tokens([str(item) for item in enable])
                if isinstance(enable, list)
                else frozenset()
            )
        )
    )


def resolve_enable(
    cli_enable: Sequence[str] | None,
    *,
    project_root: Path | None = None,
) -> frozenset[str]:
    return frozenset(
        load_enable_from_project(project_root) | parse_enable_tokens(cli_enable),
    )
