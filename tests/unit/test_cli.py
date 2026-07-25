import pytest

from shipgate.cli import main


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
