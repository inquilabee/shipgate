from shipgate.app import RunCommand, ShipGateApp
from shipgate.catalog.loader import CatalogLoader
from shipgate.runtime.executor import Executor, ProcessResult


class FakeExecutor(Executor):
    def run(self, argv, *, cwd, env=None):
        if "check" in argv:
            return ProcessResult(
                argv=argv,
                cwd=cwd,
                exit_code=0,
                stdout="[]",
                stderr="",
                duration_ms=1,
            )
        return super().run(argv, cwd=cwd, env=env)


class FailExecutor(Executor):
    def run(self, argv, *, cwd, env=None):  # ruff:ignore[no-self-use]
        _ = env
        import json

        return ProcessResult(
            argv=argv,
            cwd=cwd,
            exit_code=1,
            stdout=json.dumps(
                [
                    {
                        "code": "F401",
                        "message": "unused",
                        "filename": "app.py",
                        "location": {"row": 1, "column": 1},
                    }
                ]
            ),
            stderr="",
            duration_ms=1,
        )


def test_list_suites():
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FakeExecutor())
    output = app.list_suites()
    assert "standard" in output
    assert "python-quality" in output


def test_quiet_success_no_output(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FakeExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
            quiet=True,
        )
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_display_cli_prints_subprocess_argv(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FakeExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
            display_cli=True,
        )
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "ruff.lint:" in captured.err
    assert "ruff" in captured.err
    assert "check" in captured.err


def test_failing_report_exits_one(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FailExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
            error_format="compact",
        )
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "F401" in captured.err


def test_ci_defaults_to_github_format(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("CI", "true")
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FailExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
        )
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "::error" in captured.err


def test_quiet_failure_suppresses_stderr(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FailExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
            quiet=True,
            error_format="compact",
        )
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err == ""
