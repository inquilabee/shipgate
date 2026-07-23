"""Formatter registry."""

from shipgate.core.registry import Registry
from shipgate.formatters.compact import CompactFormatter
from shipgate.formatters.core.base import BaseFormatter
from shipgate.formatters.github import GitHubFormatter
from shipgate.formatters.json import JsonFormatter
from shipgate.formatters.text import TextFormatter

Formatter = BaseFormatter

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


def get_formatter(name: str) -> BaseFormatter:
    return FORMATTER_REGISTRY.get(name)
