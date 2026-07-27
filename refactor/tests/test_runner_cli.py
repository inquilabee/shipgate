from pathlib import Path

from refactor.cli import main
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
    assert check_paths([tmp_path]) == []


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
