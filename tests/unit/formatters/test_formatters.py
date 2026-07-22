import json

from shipgate.domain.reports import (
    CheckReport,
    Finding,
    FindingLocation,
    RunReport,
)
from shipgate.formatters.compact import CompactFormatter
from shipgate.formatters.github import GitHubFormatter
from shipgate.formatters.json import JsonFormatter
from shipgate.formatters.text import TextFormatter


def sample_report() -> RunReport:
    finding = Finding(
        check_id="ruff.lint",
        rule_id="F401",
        severity="error",
        message="Unused import",
        location=FindingLocation(path="src/app.py", line=42),
    )
    check = CheckReport(
        check_id="ruff.lint",
        tool_id="ruff.lint",
        status="failed",
        exit_code=1,
        findings=(finding,),
    )
    return RunReport(
        run_id="run", suite="standard", mode="check", status="failed", reports=(check,)
    )


def test_json_formatter():
    output = JsonFormatter().render(sample_report())
    data = json.loads(output)
    assert data["status"] == "failed"


def test_compact_formatter():
    output = CompactFormatter().render(sample_report())
    assert "src/app.py:42: error: F401 Unused import" in output


def test_text_formatter():
    output = TextFormatter().render(sample_report())
    assert "F401" in output


def test_github_escapes():
    finding = Finding(
        check_id="ruff.lint",
        rule_id="X",
        severity="error",
        message="bad: value, here",
        location=FindingLocation(path="src/a.py", line=1),
    )
    report = RunReport(
        run_id="r",
        suite=None,
        mode="check",
        status="failed",
        reports=(
            CheckReport(
                check_id="ruff.lint",
                tool_id="ruff.lint",
                status="failed",
                exit_code=1,
                findings=(finding,),
            ),
        ),
    )
    output = GitHubFormatter().render(report)
    assert "%3A" in output


def tool_exit_report() -> RunReport:
    check = CheckReport(
        check_id="shellcheck",
        tool_id="shellcheck",
        status="failed",
        exit_code=1,
        findings=(),
    )
    return RunReport(
        run_id="run",
        suite="standard",
        mode="check",
        status="failed",
        reports=(check,),
    )


def test_compact_formatter_tool_exit():
    output = CompactFormatter().render(tool_exit_report())
    assert "shellcheck: error: TOOL_EXIT Tool failed" in output


def test_text_formatter_tool_exit():
    output = TextFormatter().render(tool_exit_report())
    assert "TOOL_EXIT" in output
    assert "Tool failed" in output


def test_github_formatter_tool_exit():
    output = GitHubFormatter().render(tool_exit_report())
    assert "TOOL_EXIT" in output
    assert "Tool failed" in output


def test_get_formatter_unknown_raises():
    import pytest
    from shipgate.formatters.plugins import get_formatter

    with pytest.raises(ValueError, match="unknown error format"):
        get_formatter("xml")
