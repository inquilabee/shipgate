"""Per-tool check result cache."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.gates.runtime import is_gate_tool
from shipgate.planning.utils.gitignore import expand_scope

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

    def _cache_key(self, resolved: ResolvedRequest) -> str:
        parts: list[str] = [
            resolved.tool.id,
            resolved.mode.value,
            *sorted(str(path) for path in resolved.options.paths),
            *resolved.extra_args,
            *self._binding_parts(resolved),
            f"contents:{self._scoped_content_digest(resolved)}",
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

    def _scoped_content_digest(self, resolved: ResolvedRequest) -> str:
        blob = bytearray()
        root = resolved.project_root.resolve()
        for file_path in self._scoped_input_files(resolved):
            rel = file_path.resolve().relative_to(root).as_posix()
            blob.extend(rel.encode())
            blob.append(0)
            blob.extend(file_path.read_bytes())
            blob.append(0)
        return hashlib.sha256(blob).hexdigest()

    def _scoped_input_files(self, resolved: ResolvedRequest) -> tuple[Path, ...]:
        root = resolved.project_root.resolve()
        files: list[Path] = []
        seen: set[Path] = set()
        extensions = resolved.tool.scope.extensions
        globs = resolved.tool.scope.globs
        for raw in resolved.options.paths:
            candidate = raw if raw.is_absolute() else root / raw
            if not candidate.exists():
                continue
            resolved_candidate = candidate.resolve()
            if resolved_candidate.is_file():
                self._remember_file(resolved_candidate, files, seen)
                continue
            if not resolved_candidate.is_dir():
                continue
            for found in expand_scope(
                root,
                resolved_candidate,
                extensions=extensions,
                globs=globs,
                respect_gitignore=True,
            ):
                self._remember_file(found.resolve(), files, seen)
        files.sort(key=lambda path: path.relative_to(root).as_posix())
        return tuple(files)

    @staticmethod
    def _remember_file(path: Path, files: list[Path], seen: set[Path]) -> None:
        if path in seen:
            return
        seen.add(path)
        files.append(path)

    @staticmethod
    def _binding_parts(resolved: ResolvedRequest) -> list[str]:
        parts: list[str] = []
        if resolved.options.threshold is not None:
            parts.append(f"threshold:{resolved.options.threshold}")
        if extra := resolved.options.extra:
            parts.append("extra:" + json.dumps(extra, sort_keys=True, default=str))
        return parts

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
