"""GitHub workflow annotation formatter."""

from shipgate.domain.reports import Finding, RunReport


class GitHubFormatter:
    def render(self, report: RunReport) -> str:
        lines: list[str] = []
        for check in report.reports:
            for finding in check.findings:
                lines.append(_format_annotation(check.check_id, finding))
        return "\n".join(lines) + ("\n" if lines else "")


def _escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _format_annotation(check_id: str, finding: Finding) -> str:
    title = _escape(f"{check_id}/{finding.rule_id}")
    message = _escape(finding.message)
    if finding.location and finding.location.path:
        file_part = f"file={finding.location.path}"
        if finding.location.line is not None:
            file_part += f",line={finding.location.line}"
        return f"::{finding.severity} {file_part},title={title}::{message}"
    return f"::{finding.severity} title={title}::{message}"
