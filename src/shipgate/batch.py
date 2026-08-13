"""Batch execution from request files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from shipgate.domain.modes import RunMode
from shipgate.errors import ConfigError


@dataclass(frozen=True)
class BatchRequest:
    runnable: str
    mode: RunMode
    target: Path
    extra_args: tuple[str, ...] = ()


class BatchFileLoader:
    """Parse a YAML or JSON batch request file into ``BatchRequest`` values."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @classmethod
    def load(cls, path: Path) -> list[BatchRequest]:
        return cls(path)._load()

    def _load(self) -> list[BatchRequest]:
        text = self._path.read_text(encoding="utf-8")
        items = self._parse_items(text)
        if not isinstance(items, list):
            raise ConfigError(
                "batch file must contain a list of requests",
                path=str(self._path),
            )
        return [self._parse_item(index, item) for index, item in enumerate(items)]

    def _parse_items(self, text: str) -> object:
        if self._path.suffix in {".yaml", ".yml"}:
            raw = yaml.safe_load(text)
            return raw.get("requests", raw) if isinstance(raw, dict) else raw
        import json

        return json.loads(text)

    def _parse_item(self, index: int, item: object) -> BatchRequest:
        if not isinstance(item, dict):
            raise self._item_error(index, "must be a mapping")
        runnable = item.get("runnable")
        if not isinstance(runnable, str) or not runnable:
            raise self._item_error(index, "is missing runnable")
        mode = self._parse_mode(index, item.get("mode", "check"))
        options = item.get("options", {}) or {}
        if not isinstance(options, dict):
            raise self._item_error(index, "options must be a mapping")
        raw_paths = options.get("paths", ["."])
        paths = raw_paths if isinstance(raw_paths, list) and raw_paths else ["."]
        extra = item.get("extra_args", [])
        if not isinstance(extra, list):
            raise self._item_error(index, "extra_args must be a list")
        return BatchRequest(
            runnable=runnable,
            mode=mode,
            target=Path(str(paths[0])),
            extra_args=tuple(str(arg) for arg in extra),
        )

    def _parse_mode(self, index: int, raw: object) -> RunMode:
        try:
            return RunMode(str(raw))
        except ValueError as exc:
            raise self._item_error(index, f"has invalid mode {raw!r}") from exc

    def _item_error(self, index: int, detail: str) -> ConfigError:
        return ConfigError(f"batch request {index} {detail}", path=str(self._path))


def load_batch_file(path: Path) -> list[BatchRequest]:
    return BatchFileLoader.load(path)
