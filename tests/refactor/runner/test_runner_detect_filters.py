from __future__ import annotations

from pathlib import Path

from tests.refactor.support.still_detecting_rule import apply_still_detecting_rule

from refactor.runner import check_paths


def test_custom_detect_path_filter_not_bypassed_by_combined_visitor(
    tmp_path: Path,
) -> None:
    src = tmp_path / "module.py"
    src.write_text("def f():\n    if True:\n        return 1\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert all(hit.rule_id != "no-conditionals-in-tests" for hit in hits)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_src = tests_dir / "test_module.py"
    test_src.write_text("def test_f():\n    if True:\n        assert 1\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(hit.rule_id == "no-conditionals-in-tests" for hit in hits)


def test_apply_auto_rule_rejects_rewrite_that_still_detects() -> None:
    source = "x = HIT_MARKER\n"
    assert apply_still_detecting_rule(source, Path("sample.py")) == source
