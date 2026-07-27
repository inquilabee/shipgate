"""Shared types and constants for layout detection."""

from __future__ import annotations

from dataclasses import dataclass, field

DOC_BASENAMES = frozenset({"docs", "doc", "documentation"})
TEST_DIR_BASENAMES = frozenset({"test", "tests"})
DOC_EXTENSIONS = frozenset({".md", ".rst", ".adoc"})
UTILITY_PY_BASENAMES = frozenset(
    {
        "scripts",
        "script",
        "bin",
        "examples",
        "example",
        "sample_files",
        "samples",
        "tools",
        "migrations",
        "alembic",
    }
)
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".coverage",
        "htmlcov",
        "build",
        "dist",
        "egg-info",
        ".eggs",
        ".idea",
        ".vscode",
        ".shipgate",
        "mlruns",
        "mutants",
        ".next",
        "target",
        "vendor",
    }
)
SKIP_DIR_SUFFIXES = (".egg-info",)


@dataclass(frozen=True)
class ProjectLayout:
    """Relative posix paths for production Python, tests, and docs roots."""

    python_dirs: tuple[str, ...]
    test_dirs: tuple[str, ...]
    docs_dirs: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass
class DirSignals:
    py_files: list[str] = field(default_factory=list)
    test_py_files: list[str] = field(default_factory=list)
    prod_py_files: list[str] = field(default_factory=list)
    doc_files: list[str] = field(default_factory=list)
    has_init: bool = False
    has_conftest: bool = False
