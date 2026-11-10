import shutil
from pathlib import Path

import pytest

from shipgate.core import run_command
from shipgate.planning.utils.git_visible import GitVisibleFiles

GIT = shutil.which("git")


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_git_visible_files_agrees_with_git_check_ignore(tmp_path: Path):
    """One ls-files must answer like a check-ignore per path, nested .gitignore included."""
    write_tree(
        tmp_path,
        {
            ".gitignore": "build/\n*.log\n",
            "src/a.py": "x = 1\n",
            "src/gen_x.py": "x = 1\n",
            "src/.gitignore": "gen_*.py\n",
            "build/out.py": "x = 1\n",
            "notes.log": "n\n",
            "kept/b.py": "x = 1\n",
            "kept/deep/c.py": "x = 1\n",
        },
    )
    assert GIT is not None
    run_command([GIT, "init", "-q"], cwd=tmp_path, check=True)
    visible = GitVisibleFiles.load(tmp_path)
    assert visible is not None
    for path in sorted(tmp_path.rglob("*")):
        rel = path.relative_to(tmp_path).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        ignored = run_command([GIT, "check-ignore", "-q", rel], cwd=tmp_path).returncode == 0
        assert visible.is_ignored(rel) is ignored, rel


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_git_visible_files_keeps_tracked_files_and_is_none_outside_git(tmp_path: Path):
    assert GitVisibleFiles.load(tmp_path) is None
    write_tree(tmp_path, {".gitignore": "*.gen\n", "forced.gen": "x\n", "plain.txt": "x\n"})
    assert GIT is not None
    run_command([GIT, "init", "-q"], cwd=tmp_path, check=True)
    run_command([GIT, "add", "-f", "forced.gen"], cwd=tmp_path, check=True)
    visible = GitVisibleFiles.load(tmp_path)
    assert visible is not None
    assert not visible.is_ignored("forced.gen")
    assert not visible.is_ignored("plain.txt")
    assert visible.is_ignored("nonexistent.gen")
