"""Per-check wall time for one run, and how it is reported."""

from __future__ import annotations

import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.domain.run_command import RunCommand

SLOW_RUN_SECONDS = 10.0
SLOWEST_SHOWN = 3


class CheckTimings:
    """Thread-safe ``tool id -> seconds``; cache hits and skips simply record ~0."""

    def __init__(self) -> None:
        self._seconds: dict[str, float] = {}
        self._lock = threading.Lock()

    def record(self, tool_id: str, seconds: float) -> None:
        with self._lock:
            self._seconds[tool_id] = seconds

    def slowest(self, limit: int | None = None) -> list[tuple[str, float]]:
        with self._lock:
            ranked = sorted(self._seconds.items(), key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    def render_all(self) -> str:
        lines = [f"  {seconds:7.2f}s  {tool_id}" for tool_id, seconds in self.slowest()]
        return "shipgate timings:\n" + "\n".join(lines) + "\n"

    def render_slowest(self, total_seconds: float) -> str:
        top = ", ".join(f"{tool_id} {sec:.1f}s" for tool_id, sec in self.slowest(SLOWEST_SHOWN))
        run = f"run took {total_seconds:.1f}s; --timings for all"
        return f"shipgate: slowest checks: {top} ({run})\n"

    def emit(self, command: RunCommand, total_seconds: float) -> None:
        """``--timings`` lists every check; a slow run gets one summary line unless quiet."""
        if command.timings:
            sys.stderr.write(self.render_all())
        elif total_seconds >= SLOW_RUN_SECONDS and not command.quiet and self._seconds:
            sys.stderr.write(self.render_slowest(total_seconds))
