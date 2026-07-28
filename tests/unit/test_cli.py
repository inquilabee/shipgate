import pytest

from shipgate.cli import main, normalize_argv


def test_normalize_argv_none_uses_sys_argv(monkeypatch):
    monkeypatch.setattr("shipgate.cli.sys.argv", ["shipgate", "check", "--check", "ruff.lint"])
    assert normalize_argv(None) == ["check", "--check", "ruff.lint"]


def test_normalize_argv_empty_defaults_to_check():
    assert normalize_argv([]) == ["check"]


def test_normalize_argv_bare_target_prefixes_check():
    assert normalize_argv(["src"]) == ["check", "src"]


def test_normalize_argv_keeps_refactor_subcommand():
    assert normalize_argv(["refactor", "check", "--strict", "src"]) == [
        "refactor",
        "check",
        "--strict",
        "src",
    ]


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        raise SystemExit(main(["--help"]))
    assert exc.value.code == 0


def test_refactor_help_branded_as_shipgate(capsys):
    code = main(["refactor", "--help"])
    captured = capsys.readouterr()
    assert code == 0
    assert "shipgate refactor" in captured.out
    assert "usage: refactor" not in captured.out


def test_refactor_forwards_list(monkeypatch):
    calls: list[tuple[list[str] | None, str]] = []

    def fake_refactor_main(argv=None, *, prog="python -m refactor"):
        calls.append((argv, prog))
        return 0

    monkeypatch.setattr("refactor.cli.main", fake_refactor_main)
    code = main(["refactor", "list", "--enable", "gpsg"])
    assert code == 0
    assert calls == [(["list", "--enable", "gpsg"], "shipgate refactor")]


def test_output_dir_flag_removed():
    code = main(["check", "--output-dir", "nowhere"])
    assert code != 0


def test_list_suites(capsys):
    code = main(["list", "suites"])
    captured = capsys.readouterr()
    assert code == 0
    assert "standard" in captured.out
