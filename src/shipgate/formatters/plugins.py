"""Formatter registry."""

from shipgate.formatters.compact import CompactFormatter
from shipgate.formatters.github import GitHubFormatter
from shipgate.formatters.json import JsonFormatter
from shipgate.formatters.text import TextFormatter

FORMATTERS = {
    "json": JsonFormatter(),
    "compact": CompactFormatter(),
    "text": TextFormatter(),
    "github": GitHubFormatter(),
}


def get_formatter(name: str):
    if name not in FORMATTERS:
        return FORMATTERS["json"]
    return FORMATTERS[name]
