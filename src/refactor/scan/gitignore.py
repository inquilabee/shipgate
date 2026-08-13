"""Gitignore stacking for refactor path walks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pathspec

if TYPE_CHECKING:
    from collections.abc import Sequence

IGNORED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".shipgate",
        ".tox",
        ".venv",
        "node_modules",
        "venv",
    }
)


@dataclass(frozen=True)
class GitignoreLayer:
    base: Path
    spec: pathspec.PathSpec

    def decision(self, path: Path, *, is_dir: bool) -> bool | None:
        try:
            relative = path.relative_to(self.base).as_posix()
        except ValueError:
            return None
        check = f"{relative}/" if is_dir else relative
        last: bool | None = None
        for pattern in self.spec.patterns:
            if pattern.include is None:
                continue
            if pattern.match_file(check) is not None:
                last = pattern.include
        return last


def walk_python_files(root: Path, layers: tuple[GitignoreLayer, ...]) -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        active = layers_with_nested(layers, current_path)
        dirnames[:] = filter_walk_dirnames(dirnames, current_path, active)
        for filename in sorted(filenames):
            candidate = current_path / filename
            if candidate.suffix != ".py":
                continue
            if should_ignore_path(candidate, active, is_dir=False):
                continue
            files.append(candidate.resolve())
    return files


def layers_with_nested(
    layers: tuple[GitignoreLayer, ...],
    current_path: Path,
) -> tuple[GitignoreLayer, ...]:
    nested = gitignore_layer_at(current_path)
    return (
        layers
        if nested is None or any(layer.base == nested.base for layer in layers)
        else (*layers, nested)
    )


def gitignore_layer_at(directory: Path) -> GitignoreLayer | None:
    ignore_path = directory / ".gitignore"
    return (
        GitignoreLayer(
            base=directory,
            spec=pathspec.PathSpec.from_lines(
                "gitignore",
                ignore_path.read_text(encoding="utf-8").splitlines(),
            ),
        )
        if ignore_path.is_file()
        else None
    )


def filter_walk_dirnames(
    dirnames: list[str],
    current_path: Path,
    layers: tuple[GitignoreLayer, ...],
) -> list[str]:
    return [
        dirname
        for dirname in sorted(dirnames)
        if not should_ignore_path(current_path / dirname, layers, is_dir=True)
    ]


def load_gitignore(root: Path) -> tuple[GitignoreLayer, ...]:
    current = root.resolve()
    ancestors: list[Path] = []
    found_project = False
    for candidate in (current, *current.parents):
        ancestors.append(candidate)
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").is_file():
            found_project = True
            break
    if not found_project:
        ancestors = [current]
    return tuple(
        layer
        for candidate in reversed(ancestors)
        if (layer := gitignore_layer_at(candidate)) is not None
    )


def should_ignore_path(
    path: Path,
    layers: tuple[GitignoreLayer, ...],
    *,
    is_dir: bool,
) -> bool:
    if path.name in IGNORED_DIR_NAMES:
        return True
    ignored = False
    for layer in layers:
        decision = layer.decision(path, is_dir=is_dir)
        if decision is not None:
            ignored = decision
    return ignored


def resolved_under_roots(path: Path, roots: Sequence[Path]) -> bool:
    resolved = path.resolve()
    return any(resolved == root or resolved.is_relative_to(root) for root in roots)
