"""Shared types and constants for layout detection."""

from __future__ import annotations

from dataclasses import dataclass, field

from shipgate.planning.utils.gitignore import ignored_dir_names

DOC_BASENAMES = frozenset({"docs", "doc", "documentation", "sphinx"})
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
        "benchmarks",
        "benchmark",
        "typing_tests",
        "sphinx",
    }
)
LAYOUT_SKIP_EXTRA = frozenset(
    {
        ".hg",
        ".svn",
        "node_modules",
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
        "mlruns",
        "mutants",
        ".next",
        "target",
        "vendor",
    }
)
SKIP_DIR_NAMES = ignored_dir_names() | LAYOUT_SKIP_EXTRA
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
