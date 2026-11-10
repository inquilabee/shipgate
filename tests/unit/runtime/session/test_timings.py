from pathlib import Path

import pytest

from shipgate.domain.run_command import RunCommand
from shipgate.runtime.session.timings import SLOW_RUN_SECONDS, CheckTimings

ROOT = Path()


def filled() -> CheckTimings:
    timings = CheckTimings()
    for tool_id, seconds in (("ruff.lint", 0.4), ("ty.check", 8.2), ("radon.cc", 3.1), ("a", 0.0)):
        timings.record(tool_id, seconds)
    return timings


def test_slowest_is_ordered_longest_first():
    assert [tool_id for tool_id, _ in filled().slowest(2)] == ["ty.check", "radon.cc"]


def test_timings_flag_lists_every_check(capsys: pytest.CaptureFixture[str]):
    filled().emit(RunCommand(project_root=ROOT, timings=True), total_seconds=1.0)
    err = capsys.readouterr().err
    assert all(tool_id in err for tool_id in ("ty.check", "radon.cc", "ruff.lint", "a"))


def test_slow_run_gets_one_summary_line_and_fast_or_quiet_runs_stay_silent(
    capsys: pytest.CaptureFixture[str],
):
    slow = SLOW_RUN_SECONDS + 1
    filled().emit(RunCommand(project_root=ROOT), total_seconds=slow)
    line = capsys.readouterr().err
    assert line.count("\n") == 1
    assert line.index("ty.check") < line.index("radon.cc")

    filled().emit(RunCommand(project_root=ROOT), total_seconds=1.0)
    filled().emit(RunCommand(project_root=ROOT, quiet=True), total_seconds=slow)
    assert capsys.readouterr().err == ""
