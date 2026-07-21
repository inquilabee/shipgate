import sys
from pathlib import Path

from shipgate.runtime.executor import Executor


def test_successful_command():
    executor = Executor()
    result = executor.run(
        (sys.executable, "-c", "print('ok')"),
        cwd=Path.cwd(),
    )
    assert result.exit_code == 0
    assert "ok" in result.stdout


def test_failing_command():
    executor = Executor()
    result = executor.run(
        (sys.executable, "-c", "import sys; sys.exit(2)"),
        cwd=Path.cwd(),
    )
    assert result.exit_code == 2
