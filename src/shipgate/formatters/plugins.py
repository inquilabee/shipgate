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
    try:
        return FORMATTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown error format: {name!r}") from exc
