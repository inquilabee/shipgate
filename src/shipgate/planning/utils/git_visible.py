"""Which paths git considers not ignored, from a single ``git ls-files``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.core.process import run_command

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class GitVisibleFiles:
    """Every path git does not ignore, from one ``git ls-files`` call.

    Equivalent to ``git check-ignore`` for the question the scope walk asks
    ("may I descend into / lint this?"), including nested ``.gitignore`` files
    and ``core.excludesFile``, without a subprocess per path. Tracked files are
    never ignored, exactly as with ``check-ignore``.
    """

    def __init__(self, names: Iterable[str]) -> None:
        files: set[str] = set()
        dirs: set[str] = set()
        for name in names:
            files.add(name)
            parent = name.rpartition("/")[0]
            while parent and parent not in dirs:
                dirs.add(parent)
                parent = parent.rpartition("/")[0]
        self._files = frozenset(files)
        self._dirs = frozenset(dirs)

    @classmethod
    def load(cls, project_root: Path) -> GitVisibleFiles | None:
        """``None`` outside a git checkout or when git fails (caller falls back)."""
        if not (project_root / ".git").is_dir():
            return None
        result = run_command(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=project_root,
        )
        if result.returncode != 0:
            return None
        return cls(name for name in result.stdout.split("\0") if name)

    def is_ignored(self, rel_str: str) -> bool:
        return rel_str not in self._files and rel_str not in self._dirs
