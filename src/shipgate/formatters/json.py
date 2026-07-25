"""JSON formatter."""

import json

from shipgate.domain.reports import RunReport
from shipgate.formatters.core.base import BaseFormatter


class JsonFormatter(BaseFormatter):
    def render_lines(self, report: RunReport) -> list[str]:  # ruff:ignore[no-self-use]
        return json.dumps(report.to_dict(), indent=2).splitlines()
