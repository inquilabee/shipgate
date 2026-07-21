"""JSON formatter."""

import json

from shipgate.domain.reports import RunReport


class JsonFormatter:
    def render(self, report: RunReport) -> str:
        return json.dumps(report.to_dict(), indent=2) + "\n"
