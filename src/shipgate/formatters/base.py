"""Formatter protocol and registry."""

from typing import Protocol

from shipgate.core.registry import Registry
from shipgate.domain.reports import RunReport
from shipgate.formatters.compact import CompactFormatter
from shipgate.formatters.github import GitHubFormatter
from shipgate.formatters.json import JsonFormatter
from shipgate.formatters.text import TextFormatter


class Formatter(Protocol):
    def render(self, report: RunReport) -> str: ...


FORMATTER_REGISTRY = Registry(
    {
        "json": JsonFormatter(),
        "compact": CompactFormatter(),
        "text": TextFormatter(),
        "github": GitHubFormatter(),
    },
    unknown_message="unknown error format: {name!r}",
)
FORMATTERS = FORMATTER_REGISTRY.items()


def get_formatter(name: str) -> Formatter:
    return FORMATTER_REGISTRY.get(name)
