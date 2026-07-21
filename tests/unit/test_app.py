from shipgate.app import RunCommand, ShipGateApp
from shipgate.catalog.loader import load_catalog
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


def test_list_suites():
    app = ShipGateApp(catalog=load_catalog(), executor=FakeExecutor())
    output = app.list_suites()
    assert "standard" in output
    assert "python-quality" in output


def test_quiet_success_no_output(tmp_path, capsys):
    app = ShipGateApp(catalog=load_catalog(), executor=FakeExecutor())
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


def test_failing_report_exits_one(tmp_path, capsys):
    class FailExecutor(Executor):
        def run(self, argv, *, cwd, env=None):
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

    app = ShipGateApp(catalog=load_catalog(), executor=FailExecutor())
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
