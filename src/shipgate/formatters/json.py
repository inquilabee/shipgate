"""JSON formatter."""

from shipgate.domain.reports import RunReport
from shipgate.runtime.core.json_io import dumps_indented


class JsonFormatter:
    def render(self, report: RunReport) -> str:
        return dumps_indented(report.to_dict())
