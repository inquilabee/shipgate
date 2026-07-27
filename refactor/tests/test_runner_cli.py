from pathlib import Path

from refactor.cli import main
from refactor.registry import RULES
from refactor.runner import check_paths, fix_paths

BEFORE = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d[key] if key in d else 0
    return value
"""

AFTER = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d.get(key, 0)
    return value
"""


def test_check_paths_finds_default_get(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(h.rule_id == "default-get" for h in hits)


def test_fix_paths_rewrites_safe_rules(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == AFTER
    hits = check_paths([tmp_path])
    assert not any(hit.rule_id == "default-get" for hit in hits)


MULTI_BEFORE = """\
def f(items=[]):
    cache = dict()
"""

MULTI_AFTER = """\
def f(items=[]):
    cache = {}
"""

NON_SAFE_RULE_IDS = frozenset(rule.rule_id for rule in RULES if not rule.safe_apply)


def test_fix_paths_applies_only_safe_rules(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(MULTI_BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == MULTI_AFTER
    hits = check_paths([tmp_path])
    assert not any(hit.rule_id == "dict-literal" for hit in hits)
    assert any(hit.rule_id == "default-mutable-arg" for hit in hits)
    assert hits
    assert all(hit.rule_id in NON_SAFE_RULE_IDS for hit in hits)


def test_cli_list_includes_default_get(capsys) -> None:
    code = main(["list"])
    out = capsys.readouterr().out
    assert code == 0
    assert "default-get" in out
    assert "list-literal" in out


def test_cli_check_exit_code(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    assert main(["check", str(tmp_path)]) == 1
