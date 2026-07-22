"""Result caching."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ResultCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(argv: tuple[str, ...], cwd: Path) -> str:
        payload = json.dumps({"argv": argv, "cwd": str(cwd)}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, key: str) -> dict | None:
        path = self.root / f"{key}.json"
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put(self, key: str, data: dict) -> None:
        path = self.root / f"{key}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
