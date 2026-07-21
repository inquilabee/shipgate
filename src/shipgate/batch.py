"""Batch execution from request files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from shipgate.domain.modes import RunMode


@dataclass(frozen=True)
class BatchRequest:
    runnable: str
    mode: RunMode
    target: Path
    extra_args: tuple[str, ...] = ()


def load_batch_file(path: Path) -> list[BatchRequest]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        raw = yaml.safe_load(text)
        items = raw.get("requests", raw) if isinstance(raw, dict) else raw
    else:
        import json

        raw = json.loads(text)
        items = raw
    if not isinstance(items, list):
        raise ValueError("batch file must contain a list of requests")
    requests: list[BatchRequest] = []
    for item in items:
        options = item.get("options", {}) or {}
        paths = options.get("paths", ["."])
        target = Path(paths[0]) if paths else Path()
        requests.append(
            BatchRequest(
                runnable=str(item["runnable"]),
                mode=RunMode(item.get("mode", "check")),
                target=target,
                extra_args=tuple(item.get("extra_args", [])),
            )
        )
    return requests
