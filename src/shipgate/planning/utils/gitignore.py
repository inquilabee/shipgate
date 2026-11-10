"""Gitignore-aware path filtering."""

from __future__ import annotations

import functools
from pathlib import Path

import pathspec

from shipgate.core.process import run_command
from shipgate.paths import relative_if_under, resolve_entry, resolved_dir
from shipgate.planning.utils.git_visible import GitVisibleFiles

ANYWHERE_IGNORED = (
    ".shipgate/",
    ".venv/",
    "venv/",
    ".review-venv/",
    ".direnv/",
    ".nox/",
    ".tox/",
    "site-packages/",
    "__pycache__/",
    ".git/",
)
ROOT_ONLY_IGNORED = ("/reports/",)
DEFAULT_IGNORED = (*ANYWHERE_IGNORED, *ROOT_ONLY_IGNORED)


def default_ignores() -> tuple[str, ...]:
    return DEFAULT_IGNORED


def ignored_dir_names() -> frozenset[str]:
    return frozenset(item.strip("/") for item in ANYWHERE_IGNORED)


def matches_ignore_prefix(rel_str: str, patterns: tuple[str, ...]) -> bool:
    return any(
        rel_str == pat or rel_str.startswith(f"{pat}/")
        for pattern in patterns
        if (pat := pattern.strip("/"))
    )


class IgnoreFile:
    """One gitignore-style file under the project root."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def patterns(self) -> tuple[str, ...]:
        return (
            tuple(
                stripped
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if (stripped := line.strip()) and not stripped.startswith("#")
            )
            if self.path.is_file()
            else ()
        )


def load_gitignore_lines(project_root: Path) -> tuple[str, ...]:
    return IgnoreFile(project_root / ".gitignore").patterns()


def load_git_exclude_lines(project_root: Path) -> tuple[str, ...]:
    return IgnoreFile(project_root / ".git" / "info" / "exclude").patterns()


def load_ignore_patterns(project_root: Path) -> tuple[str, ...]:
    return (
        *default_ignores(),
        *load_gitignore_lines(project_root),
        *load_git_exclude_lines(project_root),
    )


def ignore_files_signature(project_root: Path) -> tuple[tuple[int, int] | None, ...]:
    """(mtime_ns, size) of each ignore file, so an edit invalidates the cached spec."""
    signature: list[tuple[int, int] | None] = []
    for path in (project_root / ".gitignore", project_root / ".git" / "info" / "exclude"):
        try:
            stat = path.stat()
        except OSError:
            signature.append(None)
        else:
            signature.append((stat.st_mtime_ns, stat.st_size))
    return tuple(signature)


@functools.lru_cache(maxsize=16)
def compile_ignore_spec(
    root: str, signature: tuple[tuple[int, int] | None, ...]
) -> pathspec.PathSpec | None:
    del signature  # part of the cache key only
    patterns = list(load_ignore_patterns(Path(root)))
    return pathspec.PathSpec.from_lines("gitignore", patterns) if patterns else None


def load_gitignore_spec(project_root: Path) -> pathspec.PathSpec | None:
    """The compiled ignore spec, rebuilt only when an ignore file changes."""
    return compile_ignore_spec(str(project_root), ignore_files_signature(project_root))


def is_ignored_by_git(project_root: Path, path: Path) -> bool:
    try:
        rel = resolve_entry(path).relative_to(resolved_dir(project_root))
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    result = run_command(
        ["git", "check-ignore", "-q", rel_str],
        cwd=project_root,
    )
    return result.returncode == 0


def ignored_by_git(
    project_root: Path,
    path: Path,
    rel_str: str,
    git_visible: GitVisibleFiles | None,
) -> bool:
    """Git's verdict for *path*: the shared ls-files set, else one ``check-ignore``."""
    return (project_root / ".git").is_dir() and (
        git_visible.is_ignored(rel_str)
        if git_visible is not None
        else is_ignored_by_git(project_root, path)
    )


def ignored_path_part(rel_str: str) -> bool:
    names = ignored_dir_names()
    return any(part in names or part.endswith("-venv") for part in rel_str.split("/") if part)


def should_ignore(
    project_root: Path,
    path: Path,
    *,
    extra_excludes: tuple[str, ...] = (),
    spec: pathspec.PathSpec | None = None,
    respect_gitignore: bool = True,
    git_visible: GitVisibleFiles | None = None,
) -> bool:
    return skip_scope_entry(
        project_root,
        path,
        extra_excludes=extra_excludes,
        spec=spec,
        respect_gitignore=respect_gitignore,
        git_visible=git_visible,
    )


def skip_scope_entry(
    project_root: Path,
    path: Path,
    *,
    extra_excludes: tuple[str, ...] = (),
    spec: pathspec.PathSpec | None = None,
    respect_gitignore: bool,
    git_visible: GitVisibleFiles | None = None,
) -> bool:
    try:
        rel = resolve_entry(path).relative_to(resolved_dir(project_root))
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    if ignored_path_part(rel_str) or matches_ignore_prefix(rel_str, extra_excludes):
        return True
    if not respect_gitignore:
        return False
    if matches_ignore_prefix(rel_str, default_ignores()):
        return True
    active_spec = spec if spec is not None else load_gitignore_spec(project_root)
    return (active_spec is not None and active_spec.match_file(rel_str)) or ignored_by_git(
        project_root, path, rel_str, git_visible
    )


def matches_tool_criteria(
    rel_path: str,
    *,
    extensions: tuple[str, ...] = (),
    globs: tuple[str, ...] = (),
) -> bool:
    normalized = rel_path.replace("\\", "/")
    if not extensions and not globs:
        return True
    if extensions:
        suffix = Path(normalized).suffix
        if suffix in extensions:
            return True
    if globs:
        glob_spec = pathspec.PathSpec.from_lines("gitignore", globs)
        if glob_spec.match_file(normalized):
            return True
    return False


def include_allowed(rel: str, include: tuple[str, ...]) -> bool:
    if not include:
        return True
    normalized = rel.replace("\\", "/")
    for raw in include:
        prefix = raw.replace("\\", "/").rstrip("/")
        if not prefix:
            continue
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return True
    return False


def consider_scope_file(
    path: Path,
    *,
    project_root: Path,
    paths: list[Path],
    include: tuple[str, ...],
    extensions: tuple[str, ...],
    globs: tuple[str, ...],
) -> None:
    rel_path = relative_if_under(path, project_root)
    if rel_path is None:
        return
    rel = rel_path.as_posix()
    if not include_allowed(rel, include):
        return
    if not matches_tool_criteria(rel, extensions=extensions, globs=globs):
        return
    paths.append(path)


def walk_scope_dir(
    directory: Path,
    *,
    project_root: Path,
    paths: list[Path],
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    extensions: tuple[str, ...],
    globs: tuple[str, ...],
    respect_gitignore: bool,
    spec: pathspec.PathSpec | None,
    git_visible: GitVisibleFiles | None = None,
) -> None:
    if not directory.is_dir():
        return
    for child in sorted(directory.iterdir()):
        if child.is_dir():
            from shipgate.project.layout.types import SKIP_DIR_NAMES

            if child.name in SKIP_DIR_NAMES:
                continue
        if skip_scope_entry(
            project_root,
            child,
            extra_excludes=exclude,
            spec=spec,
            respect_gitignore=respect_gitignore,
            git_visible=git_visible,
        ):
            continue
        if child.is_file():
            consider_scope_file(
                child,
                project_root=project_root,
                paths=paths,
                include=include,
                extensions=extensions,
                globs=globs,
            )
        elif child.is_dir():
            walk_scope_dir(
                child,
                project_root=project_root,
                paths=paths,
                include=include,
                exclude=exclude,
                extensions=extensions,
                globs=globs,
                respect_gitignore=respect_gitignore,
                spec=spec,
                git_visible=git_visible,
            )


def expand_scope(
    project_root: Path,
    target: Path,
    *,
    include: tuple[str, ...] = (),
    exclude: tuple[str, ...] = (),
    extensions: tuple[str, ...] = (),
    globs: tuple[str, ...] = (),
    respect_gitignore: bool = True,
    git_visible: GitVisibleFiles | None = None,
) -> tuple[Path, ...]:
    """Expand a scope target into concrete file paths.

    *git_visible* lets a run session share one ``git ls-files`` across every
    expansion; without it one is loaded here (still one subprocess, not one
    per path).
    """
    project_root = project_root.resolve()
    target = target.resolve() if target.is_absolute() else (project_root / target).resolve()
    spec = load_gitignore_spec(project_root) if respect_gitignore else None
    if respect_gitignore and git_visible is None:
        git_visible = GitVisibleFiles.load(project_root)
    paths: list[Path] = []

    if target.is_file():
        if skip_scope_entry(
            project_root,
            target,
            extra_excludes=exclude,
            spec=spec,
            respect_gitignore=respect_gitignore,
            git_visible=git_visible,
        ):
            return ()
        consider_scope_file(
            target,
            project_root=project_root,
            paths=paths,
            include=include,
            extensions=extensions,
            globs=globs,
        )
    else:
        walk_scope_dir(
            target,
            project_root=project_root,
            paths=paths,
            include=include,
            exclude=exclude,
            extensions=extensions,
            globs=globs,
            respect_gitignore=respect_gitignore,
            spec=spec,
            git_visible=git_visible,
        )
    return tuple(paths)


def minimize_covering_dirs(files: tuple[Path, ...], project_root: Path) -> tuple[Path, ...]:
    if not files:
        return ()
    project_root = project_root.resolve()
    rel_dirs: set[str] = set()
    for file_path in files:
        resolved = file_path.resolve()
        rel = resolved.relative_to(project_root).as_posix()
        parent = Path(rel).parent
        rel_dirs.add(rel if parent == Path() else str(parent))
    kept: list[str] = []
    for candidate in sorted(rel_dirs, key=lambda item: item.count("/")):
        if any(
            candidate != kept_dir
            and (candidate == kept_dir or candidate.startswith(f"{kept_dir}/"))
            for kept_dir in kept
        ):
            continue
        kept.append(candidate)
    return tuple(Path(item) for item in sorted(kept))
