from __future__ import annotations

from pathlib import Path

from tests.refactor.support.runner_fixtures import BEFORE

from refactor.cli import main, resolve_cli_paths


def test_cli_list_includes_default_get(capsys) -> None:
    code = main(["list"])
    out = capsys.readouterr().out
    assert code == 0
    assert "default-get" in out
    assert "list-literal" in out
    assert "bridge=ruff delegates_to=" in out


def test_resolve_cli_paths_defaults_to_dogfood_scope(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "refactor").mkdir(parents=True)
    (tmp_path / "tests" / "unit").mkdir()
    resolved = resolve_cli_paths([], cwd=tmp_path)
    assert resolved == [tmp_path / "src", tmp_path / "tests" / "refactor"]
    assert resolve_cli_paths([Path()], cwd=tmp_path) == resolved


def test_resolve_cli_paths_keeps_explicit_fixture_trees(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests" / "refactor").mkdir(parents=True)
    unit = tmp_path / "tests" / "unit"
    unit.mkdir()
    assert resolve_cli_paths([unit], cwd=tmp_path) == [unit]


def test_cli_check_exit_code(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    assert main(["check", str(tmp_path)]) == 1


def test_cli_check_strict_reports_suggestion_only_rules(tmp_path: Path, capsys) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        "from typing import cast\n\ndef f(raw):\n    return cast(int, raw)\n",
        encoding="utf-8",
    )
    assert main(["check", str(tmp_path)]) == 0
    assert main(["check", "--strict", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "remove-unnecessary-cast" in out
