"""Formatter protocol and registry."""

from typing import Protocol

from shipgate.domain.reports import RunReport
from shipgate.formatters.compact import CompactFormatter
from shipgate.formatters.github import GitHubFormatter
from shipgate.formatters.json import JsonFormatter
from shipgate.formatters.text import TextFormatter


class Formatter(Protocol):
    def render(self, report: RunReport) -> str: ...


FORMATTERS: dict[str, Formatter] = {
    "json": JsonFormatter(),
    "compact": CompactFormatter(),
    "text": TextFormatter(),
    "github": GitHubFormatter(),
}


def get_formatter(name: str) -> Formatter:
    try:
        return FORMATTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown error format: {name!r}") from exc
