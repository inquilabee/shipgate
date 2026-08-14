from __future__ import annotations

from tests.refactor.support.runner_fixtures import (
    AFTER,
    BEFORE,
    DEFAULT_GET_SOURCE,
    MULTI_AFTER,
    MULTI_BEFORE,
    NON_AUTO_RULE_IDS,
)

from refactor.protocol import ApplyMode, RuleKind
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
    (tmp_path / ".git").mkdir()
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == AFTER
    hits = check_paths([tmp_path])
    assert all(hit.rule_id != "dict-literal" for hit in hits)


def test_fix_paths_applies_only_safe_rules(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
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
    (tmp_path / ".git").mkdir()
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("x = dict()\n", encoding="utf-8")
    bad.write_text("def (\n", encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert good in changed
    assert good.read_text(encoding="utf-8") == "x = {}\n"
    assert bad.read_text(encoding="utf-8") == "def (\n"


def test_fix_paths_allows_orphan_tree_without_project_markers(tmp_path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("y = dict()\n", encoding="utf-8")
    changed = fix_paths([outside])
    assert outside in changed
    assert outside.read_text(encoding="utf-8") == "y = {}\n"


def test_fix_paths_does_not_write_sibling_outside_supplied_roots(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    inside = repo / "inside.py"
    inside.write_text("x = dict()\n", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("y = dict()\n", encoding="utf-8")
    changed = fix_paths([repo])
    assert inside in changed
    assert outside not in changed
    assert outside.read_text(encoding="utf-8") == "y = dict()\n"


def test_check_paths_skips_detect_crash_on_sibling(tmp_path) -> None:
    boom = tmp_path / "boom.py"
    keep = tmp_path / "keep.py"
    boom.write_bytes(b"\xff\xfe")
    keep.write_text("x = 1\n", encoding="utf-8")
    seen: list[str] = []

    class Recorder:
        rule_id = "recorder"
        kind = RuleKind.REFACTOR
        summary = "record paths"
        apply_mode = ApplyMode.AUTO

        def detect(self, source: str, path: str) -> list:
            _ = self, source
            seen.append(path)
            return []

        def apply(self, source: str, hits: object) -> str | None:
            _ = self, hits
            return source

    hits = check_paths([tmp_path], rules=(Recorder(),))
    assert any(hit.rule_id == "file-skip" and hit.location.path.endswith("boom.py") for hit in hits)
    assert any(path.endswith("keep.py") for path in seen)
    assert all(not path.endswith("boom.py") for path in seen)
