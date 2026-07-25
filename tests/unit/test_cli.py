import pytest

from shipgate.cli import main, normalize_argv


def test_normalize_argv_none_uses_sys_argv(monkeypatch):
    monkeypatch.setattr("shipgate.cli.sys.argv", ["shipgate", "check", "--check", "ruff.lint"])
    assert normalize_argv(None) == ["check", "--check", "ruff.lint"]


def test_normalize_argv_empty_defaults_to_check():
    assert normalize_argv([]) == ["check"]


def test_normalize_argv_bare_target_prefixes_check():
    assert normalize_argv(["src"]) == ["check", "src"]


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        raise SystemExit(main(["--help"]))
    assert exc.value.code == 0


def test_output_dir_flag_removed():
    code = main(["check", "--output-dir", "nowhere"])
    assert code != 0


def test_list_suites(capsys):
    code = main(["list", "suites"])
    captured = capsys.readouterr()
    assert code == 0
    assert "standard" in captured.out
