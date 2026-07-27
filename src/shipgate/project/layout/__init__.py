"""Detect project directory roles for init-time scope scaffolding.

Init-only: guesses become declared scopes in new policy. Check-time never
overrides hand-written scopes. Prefer config markers over basename heuristics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.engine import LayoutEngine
from shipgate.project.layout.types import ProjectLayout

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["ProjectLayout", "detect_layout"]


def detect_layout(project_root: Path) -> ProjectLayout:
    """Guess directory roles under *project_root* for init scope defaults."""
    return LayoutEngine(project_root).detect()
