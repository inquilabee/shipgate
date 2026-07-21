"""Human-friendly text formatter."""

from shipgate.domain.reports import RunReport


class TextFormatter:
    def render(self, report: RunReport) -> str:
        lines: list[str] = []
        for check in report.reports:
            if check.findings:
                lines.append(f"[{check.check_id}]")
            for finding in check.findings:
                loc = ""
                if finding.location:
                    loc_part = finding.location.path
                    if finding.location.line is not None:
                        loc_part += f":{finding.location.line}"
                    loc = f" ({loc_part})"
                lines.append(f"- [{finding.severity}] {finding.rule_id}: {finding.message}{loc}")
        return "\n".join(lines) + ("\n" if lines else "")
