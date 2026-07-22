"""Compact one-line-per-finding formatter."""

from shipgate.domain.reports import Finding, RunReport
from shipgate.formatters.core.iterate import TOOL_EXIT_RULE, iter_check_findings


class CompactFormatter:
    def render(self, report: RunReport) -> str:
        lines: list[str] = []
        for check, finding in iter_check_findings(report):
            if finding.rule_id == TOOL_EXIT_RULE:
                lines.append(f"{check.check_id}: error: {finding.rule_id} {finding.message}")
            else:
                lines.append(format_finding(finding))
        return "\n".join(lines) + ("\n" if lines else "")


def format_finding(finding: Finding) -> str:
    loc = finding.location
    if loc and loc.line is not None:
        return f"{loc.path}:{loc.line}: {finding.severity}: {finding.rule_id} {finding.message}"
    return f"{finding.check_id}: {finding.severity}: {finding.rule_id} {finding.message}"
