"""First-use requirements acknowledgement for the report server."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from shipgate.paths import server_dir


def requirements_path(primary: Path) -> Path:
    return server_dir(primary) / "requirements_ack.json"


def is_acknowledged(primary: Path) -> bool:
    return requirements_path(primary).is_file()


def acknowledge(primary: Path) -> None:
    path = requirements_path(primary)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"acknowledged_at": datetime.now(UTC).isoformat()}
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
