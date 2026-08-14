"""Render layout-detected directories into ShipGate named scopes for init."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.scopes import ScopeFragments, ScopeTemplateSplicer

if TYPE_CHECKING:
    from shipgate.project.layout.types import ProjectLayout

    ScopeBody = dict[str, object]

__all__ = [
    "default_scopes",
    "render_scopes_toml",
    "render_scopes_yaml",
    "replace_pyproject_scopes",
    "replace_yaml_scopes",
]


def default_scopes(layout: ProjectLayout) -> dict[str, ScopeBody]:
    """Build named scopes from a detected layout.

    Always includes ``semgrep`` at repo root. Adds ``python-src`` and a
    matching ``ty-src`` copy, plus ``python-test-src`` and ``docs`` when
    those roots exist.
    """
    return ScopeFragments(layout).default_scopes()


def render_scopes_yaml(layout: ProjectLayout) -> str:
    """YAML ``scopes:`` block (including the ``scopes:`` key)."""
    return ScopeFragments(layout).render_yaml()


def render_scopes_toml(layout: ProjectLayout) -> str:
    """TOML ``[tool.shipgate.scopes.*]`` tables for pyproject init."""
    return ScopeFragments(layout).render_toml()


def replace_yaml_scopes(template: str, scopes_block: str) -> str:
    """Replace the top-level ``scopes:`` mapping with *scopes_block*."""
    return ScopeTemplateSplicer(template).replace_yaml(scopes_block)


def replace_pyproject_scopes(template: str, scopes_block: str) -> str:
    """Replace ``[tool.shipgate.scopes.*]`` tables with *scopes_block*."""
    return ScopeTemplateSplicer(template).replace_toml(scopes_block)
