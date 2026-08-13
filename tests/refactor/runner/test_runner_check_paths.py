from __future__ import annotations

from tests.refactor.support.runner_fixtures import (
    AFTER,
    BEFORE,
    DEFAULT_GET_SOURCE,
    MULTI_AFTER,
    MULTI_BEFORE,
    NON_AUTO_RULE_IDS,
)

from refactor.registry import RULES
from refactor.runner import check_paths, check_rules, fix_paths, iter_python_files


def test_check_paths_finds_default_get(tmp_path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(DEFAULT_GET_SOURCE, encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(h.rule_id == "default-get" for h in hits)


def test_check_paths_populates_hit_location(tmp_path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(DEFAULT_GET_SOURCE, encoding="utf-8")
    hit = next(h for h in check_paths([tmp_path]) if h.rule_id == "default-get")
    assert hit.location.line == 2
    assert hit.location.column is not None


def test_default_check_rules_include_ruff_bridges() -> None:
    assert any(getattr(rule, "delegates_to", None) is not None for rule in RULES)
    assert any(getattr(rule, "delegates_to", None) is not None for rule in check_rules())
    enabled_ids = {rule.rule_id for rule in check_rules()}
    assert "no-wildcard-imports" not in enabled_ids
    assert "require-parameter-annotation" not in enabled_ids
    assert "reintroduce-else" not in enabled_ids
    assert "default-get" in enabled_ids


def test_iter_python_files_skips_gitignored_and_tool_dirs(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("ignored.py\nignored_dir/\n", encoding="utf-8")
    visible = tmp_path / "visible.py"
    ignored_file = tmp_path / "ignored.py"
    ignored_dir = tmp_path / "ignored_dir"
    venv_dir = tmp_path / ".venv"
    shipgate_tools_dir = tmp_path / ".shipgate" / "tools"
    ignored_dir.mkdir()
    venv_dir.mkdir()
    shipgate_tools_dir.mkdir(parents=True)
    visible.write_text("x = 1\n", encoding="utf-8")
    ignored_file.write_text("x = 1\n", encoding="utf-8")
    (ignored_dir / "nested.py").write_text("x = 1\n", encoding="utf-8")
    (venv_dir / "site.py").write_text("x = 1\n", encoding="utf-8")
    (shipgate_tools_dir / "tool.py").write_text("x = 1\n", encoding="utf-8")

    assert iter_python_files([tmp_path]) == [visible]


def test_fix_paths_rewrites_safe_rules(tmp_path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == AFTER
    hits = check_paths([tmp_path])
    assert all(hit.rule_id != "dict-literal" for hit in hits)


def test_fix_paths_applies_only_safe_rules(tmp_path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(MULTI_BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == MULTI_AFTER
    hits = check_paths([tmp_path])
    assert all(hit.rule_id != "dict-literal" for hit in hits)
    assert any(hit.rule_id == "default-mutable-arg" for hit in hits)
    assert hits
    assert all(hit.rule_id in NON_AUTO_RULE_IDS for hit in hits)


def test_check_paths_skips_syntax_invalid_sibling(tmp_path) -> None:
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("x = dict()\n", encoding="utf-8")
    bad.write_text("def (\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(hit.rule_id == "dict-literal" for hit in hits)


def test_fix_paths_skips_syntax_invalid_sibling(tmp_path) -> None:
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("x = dict()\n", encoding="utf-8")
    bad.write_text("def (\n", encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert good in changed
    assert good.read_text(encoding="utf-8") == "x = {}\n"
    assert bad.read_text(encoding="utf-8") == "def (\n"


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
    (root / "inside.py").write_text("x = dict()\n", encoding="utf-8")
    outside.write_text("y = dict()\n", encoding="utf-8")

    def fake_iter(_paths):
        return [root / "inside.py", outside]

    monkeypatch.setattr("refactor.runner.iter_python_files", fake_iter)
    changed = fix_paths([root])
    assert (root / "inside.py").read_text(encoding="utf-8") == "x = {}\n"
    assert outside.read_text(encoding="utf-8") == "y = dict()\n"
    assert all(path.resolve().is_relative_to(root.resolve()) for path in changed)
