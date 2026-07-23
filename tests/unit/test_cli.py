import pytest

from shipgate.cli import build_parser, main


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_output_dir_flag_removed():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["check", "--output-dir", "/tmp/out"])  # noqa: S108


def test_list_suites(capsys):
    code = main(["list", "suites"])
    captured = capsys.readouterr()
    assert code == 0
    assert "standard" in captured.out
