import shutil
import subprocess

import pytest
from shipgate.planning.incremental import filter_changed

GIT = shutil.which("git")


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_filter_changed_returns_subset(tmp_path):
    assert GIT is not None
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    source = tmp_path / "src"
    source.mkdir()
    file_a = source / "a.py"
    file_b = source / "b.py"
    file_a.write_text("x = 1\n", encoding="utf-8")
    file_b.write_text("y = 2\n", encoding="utf-8")
    subprocess.run([GIT, "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [GIT, "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        },
    )
    file_b.write_text("y = 3\n", encoding="utf-8")
    filtered = filter_changed(
        (source,),
        "HEAD",
        project_root=tmp_path,
        changed_only=True,
    )
    assert filtered == (source,)


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_filter_changed_only_returns_empty_when_no_scope_overlap(tmp_path):
    assert GIT is not None
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    source = tmp_path / "src"
    source.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    readme = docs / "readme.md"
    readme.write_text("# readme\n", encoding="utf-8")
    (source / "a.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run([GIT, "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        [GIT, "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        },
    )
    readme.write_text("# readme\n\nupdated\n", encoding="utf-8")
    filtered = filter_changed(
        (source,),
        "HEAD",
        project_root=tmp_path,
        changed_only=True,
    )
    assert filtered == ()
