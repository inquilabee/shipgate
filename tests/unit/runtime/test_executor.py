import sys
from pathlib import Path

import pytest

from shipgate.runtime.executor import CheckTimeoutError, Executor


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


def test_per_call_timeout_overrides_the_default_and_keeps_partial_output():
    executor = Executor(timeout_seconds=600)
    script = "import time; print('started', flush=True); time.sleep(30)"
    with pytest.raises(CheckTimeoutError) as caught:
        executor.run((sys.executable, "-c", script), cwd=Path.cwd(), timeout_seconds=1)
    assert caught.value.timeout_seconds == 1
    assert "started" in caught.value.stdout
