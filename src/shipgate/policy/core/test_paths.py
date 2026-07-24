"""Test-path detection for policy gates."""

from __future__ import annotations

import re

TEST_DIR_NAMES = frozenset({"test", "tests"})
# Filename contains ``test`` then later ``_`` (e.g. mytest_helper.py).
TEST_THEN_UNDERSCORE_RE = re.compile(r"test.*_")


def is_test_path(rel: str) -> bool:
    """Return True when *rel* looks like a test module path.

    Patterns:
    - path segment ``test`` or ``tests``
    - basename contains ``test_`` or ``_test``
    - basename matches ``.*test.*_``
    - basename stem ``conftest``
    """
    normalized = rel.replace("\\", "/").lstrip("./")
    parts = normalized.split("/")
    if any(part in TEST_DIR_NAMES for part in parts):
        return True
    name = parts[-1] if parts else normalized
    stem = name[:-3] if name.endswith(".py") else name
    if stem == "conftest":
        return True
    if "test_" in name or "_test" in name:
        return True
    return TEST_THEN_UNDERSCORE_RE.search(name) is not None
