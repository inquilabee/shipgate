"""Per-file content digests, reused while a file's stat is unchanged.

The check-result cache keys on the contents of every in-scope file. Reading and
hashing them all for every check on every run is the cost of a cache *hit*, so a
digest is remembered with the ``(mtime_ns, size)`` it was taken at and reused
while both still match.

A stat match alone is not proof of identical bytes: a write inside the
filesystem's timestamp granularity, right after hashing, leaves both unchanged.
Like git's index, a digest is therefore only trusted once its file was last
modified comfortably *before* the digest was taken; anything fresher is simply
hashed again.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from shipgate.paths import PROJECT_CACHE_DIR

if TYPE_CHECKING:
    from pathlib import Path

INDEX_FILENAME = "file-digests.json"
INDEX_VERSION = 1
# A file modified less than this long before it was hashed may still change within
# the same timestamp tick, so its digest is not reused.
RACY_WINDOW_NS = 2_000_000_000


@dataclass(frozen=True)
class DigestEntry:
    mtime_ns: int
    size: int
    sha256: str
    recorded_at_ns: int

    def trusted_for(self, mtime_ns: int, size: int) -> bool:
        return (
            self.mtime_ns == mtime_ns
            and self.size == size
            and self.recorded_at_ns - self.mtime_ns > RACY_WINDOW_NS
        )


class FileDigestIndex:
    """Shared, thread-safe digest memo for one project root, persisted between runs."""

    _instances: ClassVar[dict[Path, FileDigestIndex]] = {}
    _instances_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self.path = project_root / PROJECT_CACHE_DIR / INDEX_FILENAME
        self._lock = threading.Lock()
        self._entries = self._load()
        self._touched: set[str] = set()
        self._dirty = False

    @classmethod
    def for_root(cls, project_root: Path) -> FileDigestIndex:
        root = project_root.resolve()
        with cls._instances_lock:
            if root not in cls._instances:
                cls._instances[root] = cls(root)
            return cls._instances[root]

    def digest(self, path: Path, rel: str) -> str:
        """sha256 of *path*'s bytes, from the index when its stat still matches."""
        stat = path.stat()
        with self._lock:
            self._touched.add(rel)
            entry = self._entries.get(rel)
            if entry is not None and entry.trusted_for(stat.st_mtime_ns, stat.st_size):
                return entry.sha256
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        with self._lock:
            self._entries[rel] = DigestEntry(stat.st_mtime_ns, stat.st_size, sha256, time.time_ns())
            self._dirty = True
        return sha256

    def save(self) -> None:
        """Persist new digests and forget files that no longer exist; never raises."""
        with self._lock:
            if not self._dirty:
                return
            kept = {
                rel: entry
                for rel, entry in self._entries.items()
                if rel in self._touched or (self._root / rel).is_file()
            }
            payload = {
                "version": INDEX_VERSION,
                "entries": {
                    rel: [e.mtime_ns, e.size, e.sha256, e.recorded_at_ns] for rel, e in kept.items()
                },
            }
            self._entries = kept
            self._dirty = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(f".{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            return

    def _load(self) -> dict[str, DigestEntry]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return (
                {rel: DigestEntry(*values) for rel, values in raw["entries"].items()}
                if raw.get("version") == INDEX_VERSION
                else {}
            )
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return {}
