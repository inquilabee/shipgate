from pathlib import Path

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.catalog.loader import CatalogLoader
from shipgate.runtime.executor import Executor, ProcessResult


class FakeExecutor(Executor):
    def run(self, argv, *, cwd, env=None, timeout_seconds=None):
        if "check" in argv:
            return ProcessResult(
                argv=argv,
                cwd=cwd,
                exit_code=0,
                stdout="[]",
                stderr="",
                duration_ms=1,
            )
        return super().run(argv, cwd=cwd, env=env, timeout_seconds=timeout_seconds)


class FailExecutor(Executor):
    def run(self, argv, *, cwd, env=None, timeout_seconds=None):  # ruff:ignore[no-self-use]
        _ = env, timeout_seconds
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


def test_require_if_skip_prints_without_display_cli(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FakeExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="import-linter.check",
            target=tmp_path,
        )
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "import-linter.check: (skipped: no importable package in project layout)" in captured.err


def test_no_matching_files_skip_silent_without_display_cli(tmp_path, capsys):
    app = ShipGateApp(catalog=CatalogLoader.load(), executor=FakeExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="yamllint.check",
            target=tmp_path,
        )
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""


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


class StageRecorder(ShipGateApp):
    """ShipGateApp whose three stages just record that they ran and return a set code."""

    def __init__(self, codes: dict[str, int]) -> None:
        super().__init__()
        self.codes = codes
        self.calls: list[tuple[str, str | None]] = []

    def install(self, command: InstallCommand) -> int:
        self.calls.append(("install", command.suite))
        return self.codes.get("install", 0)

    def format(self, command: RunCommand) -> int:
        self.calls.append(("format", command.suite))
        return self.codes.get("format", 0)

    def check(self, command: RunCommand) -> int:
        self.calls.append(("check", command.suite))
        return self.codes.get("check", 0)


def test_precommit_runs_install_then_format_then_check(tmp_path: Path):
    app = StageRecorder({})
    code = app.precommit(RunCommand(project_root=tmp_path, suite="standard"))
    # Format always uses its own suite; the requested suite picks the install and the check.
    assert (code, app.calls) == (
        0,
        [("install", "standard"), ("format", None), ("check", "standard")],
    )


def test_precommit_stops_at_the_first_failing_stage_and_returns_its_code(tmp_path: Path):
    app = StageRecorder({"format": 3})
    assert app.precommit(RunCommand(project_root=tmp_path)) == 3
    assert [stage for stage, _ in app.calls] == ["install", "format"]
