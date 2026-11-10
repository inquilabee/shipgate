import hashlib
import os
from pathlib import Path

import pytest

from shipgate.runtime.cache.file_digests import RACY_WINDOW_NS, FileDigestIndex


def settled_file(root: Path, rel: str, content: str) -> Path:
    """A file whose mtime is well before 'now', so its digest may be reused."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    old = path.stat().st_mtime_ns - 10 * RACY_WINDOW_NS
    os.utime(path, ns=(old, old))
    return path


@pytest.fixture
def read_counter(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    reads: list[Path] = []
    original = Path.read_bytes

    def counting(self: Path) -> bytes:
        reads.append(self)
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", counting)
    return reads


def test_unchanged_settled_file_is_not_read_again(tmp_path: Path, read_counter: list[Path]):
    path = settled_file(tmp_path, "a.yaml", "key: 1\n")
    index = FileDigestIndex(tmp_path)
    first = index.digest(path, "a.yaml")
    second = index.digest(path, "a.yaml")
    assert first == second == hashlib.sha256(b"key: 1\n").hexdigest()
    assert read_counter == [path]


def test_same_size_same_mtime_edit_is_never_served_stale(tmp_path: Path):
    """A write inside the timestamp tick leaves stat unchanged; the racy rule must catch it."""
    path = tmp_path / "a.yaml"
    path.write_text("aaaa", encoding="utf-8")
    index = FileDigestIndex(tmp_path)
    before = index.digest(path, "a.yaml")
    stat = path.stat()
    path.write_text("bbbb", encoding="utf-8")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert path.stat().st_size == stat.st_size
    assert index.digest(path, "a.yaml") != before


def test_digest_follows_content_when_stat_changes(tmp_path: Path):
    path = settled_file(tmp_path, "a.yaml", "one\n")
    index = FileDigestIndex(tmp_path)
    before = index.digest(path, "a.yaml")
    path.write_text("two two\n", encoding="utf-8")
    assert index.digest(path, "a.yaml") != before


def test_index_persists_and_survives_a_corrupt_file(tmp_path: Path, read_counter: list[Path]):
    path = settled_file(tmp_path, "a.yaml", "key: 1\n")
    index = FileDigestIndex(tmp_path)
    expected = index.digest(path, "a.yaml")
    index.save()
    read_counter.clear()

    reloaded = FileDigestIndex(tmp_path)
    assert reloaded.digest(path, "a.yaml") == expected
    assert read_counter == []

    index.path.write_text("{not json", encoding="utf-8")
    assert FileDigestIndex(tmp_path).digest(path, "a.yaml") == expected


def test_save_forgets_deleted_files(tmp_path: Path):
    gone = settled_file(tmp_path, "gone.yaml", "x\n")
    kept = settled_file(tmp_path, "kept.yaml", "y\n")
    first = FileDigestIndex(tmp_path)
    first.digest(gone, "gone.yaml")
    first.digest(kept, "kept.yaml")
    first.save()
    gone.unlink()

    second = FileDigestIndex(tmp_path)
    second.digest(kept, "kept.yaml")
    second._dirty = True
    second.save()
    assert "gone.yaml" not in FileDigestIndex(tmp_path)._entries
