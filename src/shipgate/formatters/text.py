"""Human-friendly text formatter."""

from shipgate.domain.reports import RunReport
from shipgate.formatters.core.base import BaseFormatter
from shipgate.formatters.core.iterate import TOOL_EXIT_RULE, check_has_output


class TextFormatter(BaseFormatter):
    def render_lines(self, report: RunReport) -> list[str]:
        lines: list[str] = []
        seen_headers: set[str] = set()
        for check, finding in self.iter_findings(report):
            if check.check_id not in seen_headers and check_has_output(check):
                lines.append(f"[{check.check_id}]")
                seen_headers.add(check.check_id)
            loc = ""
            if finding.location:
                loc_part = finding.location.path
                if finding.location.line is not None:
                    loc_part += f":{finding.location.line}"
                loc = f" ({loc_part})"
            if finding.rule_id == TOOL_EXIT_RULE:
                lines.append(f"- [error] {finding.rule_id}: {finding.message}")
            else:
                lines.append(f"- [{finding.severity}] {finding.rule_id}: {finding.message}{loc}")
        return lines
