from pathlib import Path

from shipgate.planning.gitignore import (
    expand_scope,
    matches_tool_criteria,
    should_ignore,
)


def test_should_ignore_shipgate_dir(tmp_path: Path):
    ignored = tmp_path / ".shipgate" / "cache"
    ignored.mkdir(parents=True)
    assert should_ignore(tmp_path, ignored)


def test_should_ignore_venv_dirs(tmp_path: Path):
    dot_venv = tmp_path / ".venv" / "lib"
    dot_venv.mkdir(parents=True)
    plain_venv = tmp_path / "venv" / "lib"
    plain_venv.mkdir(parents=True)
    assert should_ignore(tmp_path, dot_venv)
    assert should_ignore(tmp_path, plain_venv)


def test_expand_scope_respects_gitignore(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "bad.py").write_text("y = 2\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path)
    names = {p.name for p in paths}
    assert "ok.py" in names
    assert "bad.py" not in names


def test_matches_tool_criteria_glob(tmp_path: Path):
    rel = ".cursor/rules/foo.mdc"
    assert matches_tool_criteria(rel, globs=("**/*.mdc",))
    assert not matches_tool_criteria("docs/readme.md", globs=("**/*.mdc",))
