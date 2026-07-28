"""Compact one-line-per-finding formatter."""

from shipgate.domain.reports import Finding, RunReport
from shipgate.formatters.core.base import BaseFormatter
from shipgate.formatters.core.iterate import TOOL_EXIT_RULE


class CompactFormatter(BaseFormatter):
    def render_lines(self, report: RunReport) -> list[str]:
        lines: list[str] = []
        for check, finding in self.iter_findings(report):
            if finding.rule_id == TOOL_EXIT_RULE:
                lines.append(f"{check.check_id}: error: {finding.rule_id} {finding.message}")
            else:
                lines.append(self.format_finding(finding))
        return lines

    @staticmethod
    def format_finding(finding: Finding) -> str:
        loc = finding.location
        return (
            f"{loc.path}:{loc.line}: {finding.severity}: {finding.rule_id} {finding.message}"
            if loc and loc.line is not None
            else f"{finding.check_id}: {finding.severity}: {finding.rule_id} {finding.message}"
        )
