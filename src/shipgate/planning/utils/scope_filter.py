"""Scope expansion starting from a known candidate set instead of a tree walk."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.planning.utils.git_visible import GitVisibleFiles
from shipgate.planning.utils.gitignore import (
    consider_scope_file,
    load_gitignore_spec,
    skip_scope_entry,
)
from shipgate.project.layout.types import SKIP_DIR_NAMES

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    import pathspec


class ScopeFilter:
    """The walk's per-entry rules, applied to candidates and their parent dirs."""

    def __init__(
        self,
        project_root: Path,
        target: Path,
        *,
        exclude: tuple[str, ...] = (),
        respect_gitignore: bool = True,
        git_visible: GitVisibleFiles | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.target = (
            target.resolve() if target.is_absolute() else (self.project_root / target).resolve()
        )
        self.exclude = exclude
        self.respect_gitignore = respect_gitignore
        self.spec: pathspec.PathSpec | None = (
            load_gitignore_spec(self.project_root) if respect_gitignore else None
        )
        self.git_visible = (
            GitVisibleFiles.load(self.project_root)
            if respect_gitignore and git_visible is None
            else git_visible
        )
        self._skipped: dict[Path, bool] = {}

    def skips(self, path: Path) -> bool:
        if path not in self._skipped:
            self._skipped[path] = skip_scope_entry(
                self.project_root,
                path,
                extra_excludes=self.exclude,
                spec=self.spec,
                respect_gitignore=self.respect_gitignore,
                git_visible=self.git_visible,
            )
        return self._skipped[path]

    def path_chain(self, path: Path) -> list[Path] | None:
        """*path* and each directory above it below the target, or ``None`` if outside."""
        inside = path.is_file() and (path == self.target or self.target in path.parents)
        return [path, *(p for p in path.parents if self.target in p.parents)] if inside else None

    def accepts(self, path: Path) -> bool:
        chain = self.path_chain(path)
        return (
            chain is not None
            and all(parent.name not in SKIP_DIR_NAMES for parent in chain[1:])
            and all(not self.skips(entry) for entry in chain)
        )


def filter_scope_files(
    project_root: Path,
    target: Path,
    candidates: Iterable[str],
    *,
    include: tuple[str, ...] = (),
    exclude: tuple[str, ...] = (),
    extensions: tuple[str, ...] = (),
    globs: tuple[str, ...] = (),
    respect_gitignore: bool = True,
    git_visible: GitVisibleFiles | None = None,
) -> tuple[Path, ...]:
    """``expand_scope`` restricted to *candidates* (project-relative posix paths).

    Equals ``expand_scope`` intersected with the candidates, in the walk's order,
    without visiting the rest of the tree.
    """
    scope = ScopeFilter(
        project_root,
        target,
        exclude=exclude,
        respect_gitignore=respect_gitignore,
        git_visible=git_visible,
    )
    matched: list[Path] = []
    for rel in candidates:
        path = scope.project_root / rel
        if scope.accepts(path):
            consider_scope_file(
                path,
                project_root=scope.project_root,
                paths=matched,
                include=include,
                extensions=extensions,
                globs=globs,
            )
    return tuple(sorted(matched, key=lambda found: found.relative_to(scope.project_root).parts))
