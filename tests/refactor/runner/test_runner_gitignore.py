from __future__ import annotations

from refactor.runner import check_paths, fix_paths, iter_python_files


def test_collect_python_honors_parent_gitignore(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("src/generated.py\n", encoding="utf-8")
    nested = tmp_path / "src"
    nested.mkdir()
    skipped = nested / "generated.py"
    kept = nested / "keep.py"
    skipped.write_text("x = 1\n", encoding="utf-8")
    kept.write_text("x = 1\n", encoding="utf-8")
    assert iter_python_files([nested]) == [kept.resolve()]


def test_collect_python_merges_nested_and_root_gitignore(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("src/generated.py\n", encoding="utf-8")
    nested = tmp_path / "src"
    nested.mkdir()
    (nested / ".gitignore").write_text("local.py\n", encoding="utf-8")
    generated = nested / "generated.py"
    local = nested / "local.py"
    kept = nested / "keep.py"
    generated.write_text("x = 1\n", encoding="utf-8")
    local.write_text("x = 1\n", encoding="utf-8")
    kept.write_text("x = 1\n", encoding="utf-8")
    assert iter_python_files([nested]) == [kept.resolve()]


def test_fix_paths_refuses_write_outside_supplied_root(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside.py"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "inside.py").write_text("x = dict()\n", encoding="utf-8")
    outside.write_text("y = dict()\n", encoding="utf-8")

    def fake_iter(_paths):
        return [root / "inside.py", outside]

    monkeypatch.setattr("refactor.runner.iter_python_files", fake_iter)
    changed = fix_paths([root])
    assert (root / "inside.py").read_text(encoding="utf-8") == "x = {}\n"
    assert outside.read_text(encoding="utf-8") == "y = dict()\n"
    assert all(path.resolve().is_relative_to(root.resolve()) for path in changed)


def test_check_paths_refuses_read_outside_supplied_root(tmp_path, monkeypatch) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside.py"
    root.mkdir()
    (root / ".git").mkdir()
    (root / "inside.py").write_text("x = dict()\n", encoding="utf-8")
    outside.write_text("y = dict()\n", encoding="utf-8")

    def fake_iter(_paths):
        return [root / "inside.py", outside]

    monkeypatch.setattr("refactor.runner.iter_python_files", fake_iter)
    hits = check_paths([root])
    assert all(not str(hit.location.path).endswith("outside.py") for hit in hits)
    assert any(hit.rule_id == "dict-literal" for hit in hits)


def test_iter_python_files_ignores_parent_gitignore_without_project_root(tmp_path) -> None:
    (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")
    nested = tmp_path / "proj"
    nested.mkdir()
    kept = nested / "keep.py"
    kept.write_text("x = 1\n", encoding="utf-8")
    assert iter_python_files([nested]) == [kept.resolve()]


def test_nested_gitignore_unignores_keep_py(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")
    nested = tmp_path / "src"
    nested.mkdir()
    (nested / ".gitignore").write_text("!keep.py\n", encoding="utf-8")
    keep = nested / "keep.py"
    drop = nested / "drop.py"
    keep.write_text("x = 1\n", encoding="utf-8")
    drop.write_text("x = 1\n", encoding="utf-8")
    assert iter_python_files([tmp_path]) == [keep.resolve()]
