"""Formatter base class and protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from shipgate.formatters.core.iterate import iter_check_findings

if TYPE_CHECKING:
    from shipgate.domain.reports import RunReport


class BaseFormatter(ABC):
    trailing_newline = True

    def render(self, report: RunReport) -> str:
        lines = list(self.render_lines(report))
        if not lines:
            return ""
        text = "\n".join(lines)
        if self.trailing_newline:
            text += "\n"
        return text

    @abstractmethod
    def render_lines(self, report: RunReport) -> list[str]:
        raise NotImplementedError

    def iter_findings(self, report: RunReport):
        return iter_check_findings(report)
