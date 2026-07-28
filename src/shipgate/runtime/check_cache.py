"""Per-tool check result cache."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.gates.runtime import is_gate_tool

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.reports import CheckReport


class CheckResultCache:
    def __init__(self, project_root: Path, *, disabled: bool = False) -> None:
        self._root = project_root / ".shipgate" / "cache" / "check-results"
        self._disabled = disabled

    def lookup(self, resolved: ResolvedRequest) -> CheckReport | None:
        if self._disabled or not self._is_cacheable(resolved):
            return None
        path = self._entry_path(resolved)
        if not path.is_file():
            return None
        if self._is_expired(path, resolved):
            return None
        from shipgate.domain.reports import CheckReport

        payload = json.loads(path.read_text(encoding="utf-8"))
        return CheckReport.from_dict(payload)

    def store(self, resolved: ResolvedRequest, report: CheckReport) -> None:
        if self._disabled or not self._is_cacheable(resolved):
            return
        path = self._entry_path(resolved)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    def _entry_path(self, resolved: ResolvedRequest) -> Path:
        return self._root / f"{self._cache_key(resolved)}.json"

    @staticmethod
    def _cache_key(resolved: ResolvedRequest) -> str:
        parts: list[str] = [
            resolved.tool.id,
            resolved.mode.value,
            *sorted(str(path) for path in resolved.options.paths),
            *resolved.extra_args,
        ]
        if resolved.tool.install is not None and resolved.tool.install.version:
            parts.append(f"version:{resolved.tool.install.version}")
        for config_path in resolved.options.config:
            config = Path(config_path)
            candidate = config if config.is_absolute() else resolved.project_root / config
            if candidate.is_file():
                parts.append(hashlib.sha256(candidate.read_bytes()).hexdigest())
        digest = hashlib.sha256("\n".join(parts).encode()).hexdigest()
        return f"{resolved.tool.id}-{digest[:16]}"

    @staticmethod
    def _is_expired(path: Path, resolved: ResolvedRequest) -> bool:
        cache = resolved.tool.cache
        if cache is None or cache.ttl_seconds is None:
            return False
        age = time.time() - path.stat().st_mtime
        return age > cache.ttl_seconds

    @staticmethod
    def _is_cacheable(resolved: ResolvedRequest) -> bool:
        return (
            False
            if resolved.mode == RunMode.APPLY
            else (
                False
                if is_gate_tool(resolved.tool)
                else (
                    False
                    if resolved.tool.cache is not None and not resolved.tool.cache.results
                    else (
                        False
                        if resolved.tool.scope.delivery == "root"
                        else any(resolved.options.paths)
                    )
                )
            )
        )
