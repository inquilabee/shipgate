"""Shared iteration over run report findings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, RunReport

if TYPE_CHECKING:
    from collections.abc import Iterator

TOOL_EXIT_RULE = "TOOL_EXIT"
TOOL_EXIT_MESSAGE = "Tool failed"


def tool_exit_finding(check: CheckReport) -> Finding:
    return Finding(
        check_id=check.check_id,
        rule_id=TOOL_EXIT_RULE,
        severity="error",
        message=TOOL_EXIT_MESSAGE,
    )


def check_has_output(check: CheckReport) -> bool:
    return True if check.findings else check.status not in {"passed", "skipped"}


def iter_check_findings(report: RunReport) -> Iterator[tuple[CheckReport, Finding]]:
    for check in report.reports:
        if check.findings:
            for finding in check.findings:
                yield check, finding
        elif check.status not in {"passed", "skipped"}:
            yield check, tool_exit_finding(check)
