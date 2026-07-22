import pytest

from shipgate.cli import main


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_list_suites(capsys):
    code = main(["list", "suites"])
    captured = capsys.readouterr()
    assert code == 0
    assert "standard" in captured.out
