"""Compact one-line-per-finding formatter."""

from shipgate.domain.reports import Finding, RunReport


class CompactFormatter:
    def render(self, report: RunReport) -> str:
        lines: list[str] = []
        for check in report.reports:
            for finding in check.findings:
                lines.append(_format_finding(finding))
            if not check.findings and check.status != "passed":
                lines.append(f"{check.check_id}: error: TOOL_EXIT Tool failed")
        return "\n".join(lines) + ("\n" if lines else "")


def _format_finding(finding: Finding) -> str:
    loc = finding.location
    if loc and loc.line is not None:
        return f"{loc.path}:{loc.line}: {finding.severity}: {finding.rule_id} {finding.message}"
    return f"{finding.check_id}: {finding.severity}: {finding.rule_id} {finding.message}"
