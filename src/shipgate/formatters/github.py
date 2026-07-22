"""GitHub workflow annotation formatter."""

from shipgate.domain.reports import Finding, RunReport
from shipgate.formatters.core.iterate import TOOL_EXIT_RULE, iter_check_findings


class GitHubFormatter:
    def render(self, report: RunReport) -> str:
        lines: list[str] = []
        for check, finding in iter_check_findings(report):
            if finding.rule_id == TOOL_EXIT_RULE:
                title = escape(f"{check.check_id}/{finding.rule_id}")
                message = escape(finding.message)
                lines.append(f"::error title={title}::{message}")
            else:
                lines.append(format_annotation(check.check_id, finding))
        return "\n".join(lines) + ("\n" if lines else "")


def escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def format_annotation(check_id: str, finding: Finding) -> str:
    title = escape(f"{check_id}/{finding.rule_id}")
    message = escape(finding.message)
    if finding.location and finding.location.path:
        file_part = f"file={finding.location.path}"
        if finding.location.line is not None:
            file_part += f",line={finding.location.line}"
        return f"::{finding.severity} {file_part},title={title}::{message}"
    return f"::{finding.severity} title={title}::{message}"
