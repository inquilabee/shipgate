import shutil
from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.core import run_command
from shipgate.domain.modes import RunMode
from shipgate.domain.project import Scope
from shipgate.errors import PlanningError
from shipgate.planning.utils.incremental import (
    git_changed_files,
    tool_paths_after_incremental,
)

GIT = shutil.which("git")
GIT_LEAK_PREFIXES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
)
GIT_ENV = {
    key: value
    for key, value in __import__("os").environ.items()
    if not key.startswith(GIT_LEAK_PREFIXES) and key != "GIT_PREFIX"
}
GIT_ENV.update(
    {
        "GIT_AUTHOR_NAME": "t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
)


def git_init_commit(tmp_path):
    assert GIT is not None
    run_command([GIT, "init"], cwd=tmp_path, check=True)
    run_command([GIT, "add", "."], cwd=tmp_path, check=True)
    run_command(
        [GIT, "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        env=GIT_ENV,
    )


def git_add(tmp_path, *paths: Path) -> None:
    assert GIT is not None
    run_command([GIT, "add", *[str(path) for path in paths]], cwd=tmp_path, check=True)


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_git_changed_files_includes_staged_changes(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("x = 1\n", encoding="utf-8")
    git_init_commit(tmp_path)
    changed_file = source / "b.py"
    changed_file.write_text("y = 2\n", encoding="utf-8")
    git_add(tmp_path, changed_file)
    changed = git_changed_files(tmp_path, "HEAD")
    assert "src/b.py" in changed


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_invalid_since_raises_planning_error(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("x = 1\n", encoding="utf-8")
    git_init_commit(tmp_path)
    with pytest.raises(PlanningError, match=r"since|git|ref"):
        git_changed_files(tmp_path, "this-ref-does-not-exist-zz")


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_git_changed_files_includes_untracked(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("x = 1\n", encoding="utf-8")
    git_init_commit(tmp_path)
    untracked = source / "new.py"
    untracked.write_text("z = 3\n", encoding="utf-8")
    changed = git_changed_files(tmp_path, "HEAD")
    assert "src/new.py" in changed


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_tool_paths_after_incremental_root_delivery_uses_changed_files(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ruff.lint")
    source = tmp_path / "src"
    source.mkdir()
    file_a = source / "a.py"
    file_b = source / "b.py"
    file_a.write_text("x = 1\n", encoding="utf-8")
    file_b.write_text("y = 2\n", encoding="utf-8")
    git_init_commit(tmp_path)
    file_b.write_text("y = 3\n", encoding="utf-8")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = tool_paths_after_incremental(
        (Path(),),
        tool=tool,
        scope=scope,
        project_root=tmp_path,
        mode=RunMode.CHECK,
        since=None,
        changed_only=True,
    )
    assert paths == (Path("src/b.py"),)


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_aggregate_root_keeps_planned_paths_under_changed_only(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("deptry.check")
    source = tmp_path / "src"
    source.mkdir()
    file_a = source / "a.py"
    file_a.write_text("x = 1\n", encoding="utf-8")
    git_init_commit(tmp_path)
    file_a.write_text("x = 2\n", encoding="utf-8")
    scope = Scope(target=source, respect_gitignore=True)
    paths = tool_paths_after_incremental(
        (Path("src"),),
        tool=tool,
        scope=scope,
        project_root=tmp_path,
        mode=RunMode.CHECK,
        since=None,
        changed_only=True,
    )
    assert paths == (Path("src"),)
