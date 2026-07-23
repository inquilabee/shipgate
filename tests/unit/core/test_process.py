"""Tests for shipgate.core.process.run_command."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from shipgate.core import run_command
from shipgate.core.process import run_command as run_command_direct


def test_run_command_rejects_string_argv() -> None:
    with pytest.raises(TypeError, match="sequence of strings"):
        run_command("echo hi")  # type: ignore[arg-type]


def test_run_command_defaults_and_no_shell() -> None:
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value = object()
        run_command_direct(["true"])
    mock_run.assert_called_once_with(
        ["true"],
        cwd=None,
        env=None,
        timeout=None,
        check=False,
        capture_output=True,
        text=True,
        input=None,
        shell=False,
    )


def test_run_command_forwards_kwargs(tmp_path: Path) -> None:
    env = {"PATH": "/usr/bin", "SHIPGATE_TEST": "1"}
    with patch.object(subprocess, "run") as mock_run:
        mock_run.return_value = object()
        run_command_direct(
            ["git", "status"],
            cwd=tmp_path,
            env=env,
            timeout=12.5,
            check=True,
            capture_output=False,
            text=False,
            input="stdin",
        )
    mock_run.assert_called_once_with(
        ["git", "status"],
        cwd=tmp_path,
        env=env,
        timeout=12.5,
        check=True,
        capture_output=False,
        text=False,
        input="stdin",
        shell=False,
    )


def test_run_command_package_export() -> None:
    assert run_command is run_command_direct
