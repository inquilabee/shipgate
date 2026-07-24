import shutil
from pathlib import Path

import pytest

from shipgate.core import run_command
from shipgate.planning.core.scope_resolver import ScopeResolver
from shipgate.planning.utils.incremental import RunScopeSession

GIT = shutil.which("git")
GIT_ENV = {
    **__import__("os").environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def git_init_commit(tmp_path: Path) -> None:
    assert GIT is not None
    run_command([GIT, "init"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    run_command([GIT, "add", "."], cwd=tmp_path, check=True)
    run_command(
        [GIT, "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        env=GIT_ENV,
    )


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_scope_session_marks_incremental_clean_when_no_changes(tmp_path: Path):
    git_init_commit(tmp_path)
    session = RunScopeSession(
        project_root=tmp_path,
        changed_only=True,
        since=None,
    )
    assert session.is_incremental_clean() is True


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_scope_session_caches_expand_scope(tmp_path: Path):
    git_init_commit(tmp_path)
    session = RunScopeSession(
        project_root=tmp_path,
        changed_only=False,
        since=None,
    )
    target = tmp_path / "src"
    resolver = ScopeResolver(tmp_path, scope_session=session)
    first = resolver._expand_scope(
        target, extensions=(".py",), include=(), exclude=(), globs=(), respect_gitignore=True
    )
    second = resolver._expand_scope(
        target, extensions=(".py",), include=(), exclude=(), globs=(), respect_gitignore=True
    )
    assert first == second
    assert len(session.expand_cache) == 1
