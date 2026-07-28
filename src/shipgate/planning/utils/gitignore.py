"""Gitignore-aware path filtering."""

from __future__ import annotations

from pathlib import Path

import pathspec

from shipgate.core.process import run_command

DEFAULT_IGNORED = (
    ".shipgate/",
    ".venv/",
    "venv/",
    "reports/",
    "__pycache__/",
    ".git/",
)


def default_ignores() -> tuple[str, ...]:
    return DEFAULT_IGNORED


def load_gitignore_lines(project_root: Path) -> tuple[str, ...]:
    gitignore = project_root / ".gitignore"
    if not gitignore.is_file():
        return ()
    patterns: list[str] = []
    for line in gitignore.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return tuple(patterns)


def load_gitignore_spec(project_root: Path) -> pathspec.PathSpec | None:
    patterns = list(load_gitignore_lines(project_root))
    return pathspec.PathSpec.from_lines("gitignore", patterns) if patterns else None


def is_ignored_by_git(project_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    result = run_command(
        ["git", "check-ignore", "-q", rel_str],
        cwd=project_root,
    )
    return result.returncode == 0


def should_ignore(
    project_root: Path,
    path: Path,
    *,
    extra_excludes: tuple[str, ...] = (),
    spec: pathspec.PathSpec | None = None,
) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    for pattern in (*default_ignores(), *extra_excludes):
        pat = pattern.rstrip("/")
        if rel_str == pat or rel_str.startswith(f"{pat}/"):
            return True
    if spec is not None and spec.match_file(rel_str):
        return True
    git_dir = project_root / ".git"
    return is_ignored_by_git(project_root, path) if git_dir.is_dir() else False


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
    return any(rel.startswith(inc.rstrip("/")) for inc in include) if include else True


def consider_scope_file(
    path: Path,
    *,
    project_root: Path,
    paths: list[Path],
    include: tuple[str, ...],
    extensions: tuple[str, ...],
    globs: tuple[str, ...],
) -> None:
    rel = str(path.relative_to(project_root)).replace("\\", "/")
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
) -> None:
    if not directory.is_dir():
        return
    for child in sorted(directory.iterdir()):
        if respect_gitignore and should_ignore(
            project_root, child, extra_excludes=exclude, spec=spec
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
) -> tuple[Path, ...]:
    """Expand a scope target into concrete file paths."""
    project_root = project_root.resolve()
    target = target.resolve() if target.is_absolute() else (project_root / target).resolve()
    spec = load_gitignore_spec(project_root) if respect_gitignore else None
    paths: list[Path] = []

    if target.is_file():
        if respect_gitignore and should_ignore(
            project_root, target, extra_excludes=exclude, spec=spec
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
        parent = str(Path(rel).parent)
        rel_dirs.add("." if parent == "." else parent)
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
