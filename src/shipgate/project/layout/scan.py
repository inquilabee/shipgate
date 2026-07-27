"""Filesystem scan and pytest config helpers for layout detection."""

from __future__ import annotations

import os
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.planning.utils.gitignore import load_gitignore_spec
from shipgate.policy.core.test_paths import is_test_path
from shipgate.project.layout.types import (
    DOC_EXTENSIONS,
    SKIP_DIR_NAMES,
    SKIP_DIR_SUFFIXES,
    DirSignals,
)

if TYPE_CHECKING:
    import pathspec

PYTEST_INI_NAMES = ("pytest.ini", "tox.ini")
PYTEST_SECTIONS = frozenset({"[pytest]", "[tool:pytest]"})


class LayoutScanner:
    """Collect directory signals and pytest path settings for one project root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def parse_pytest(self) -> tuple[list[str], list[str]]:
        testpaths, python_files = self.pytest_pyproject()
        ini_paths, ini_files = self.pytest_ini()
        return testpaths or ini_paths, python_files or ini_files

    def pytest_pyproject(self) -> tuple[list[str], list[str]]:
        path = self.root / "pyproject.toml"
        if not path.is_file():
            return [], []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return [], []
        opts = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
        if not isinstance(opts, dict):
            return [], []
        return self.as_str_list(opts.get("testpaths")), self.as_str_list(opts.get("python_files"))

    def pytest_ini(self) -> tuple[list[str], list[str]]:
        testpaths: list[str] = []
        python_files: list[str] = []
        for name in PYTEST_INI_NAMES:
            ini = self.root / name
            if not ini.is_file():
                continue
            self.read_pytest_ini_file(ini, testpaths, python_files)
        return testpaths, python_files

    def read_pytest_ini_file(
        self,
        ini: Path,
        testpaths: list[str],
        python_files: list[str],
    ) -> None:
        _ = self
        section = False
        for line in ini.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                section = stripped.lower() in PYTEST_SECTIONS
                continue
            self.apply_pytest_ini_line(
                stripped,
                section=section,
                testpaths=testpaths,
                python_files=python_files,
            )

    @staticmethod
    def apply_pytest_ini_line(
        stripped: str,
        *,
        section: bool,
        testpaths: list[str],
        python_files: list[str],
    ) -> None:
        if not section or "=" not in stripped:
            return
        key, _, value = stripped.partition("=")
        key, value = key.strip().lower(), value.strip()
        if key == "testpaths" and not testpaths:
            testpaths[:] = value.split()
        elif key == "python_files" and not python_files:
            python_files[:] = value.split()

    def as_str_list(self, raw: object) -> list[str]:
        _ = self
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, list):
            return [str(item) for item in raw]
        return []

    def docs_markers(self) -> list[str]:
        found: list[str] = []
        if (self.root / "mkdocs.yml").is_file() or (self.root / "mkdocs.yaml").is_file():
            found.append("docs")
        if (self.root / "docs" / "conf.py").is_file():
            found.append("docs")
        if (self.root / "doc" / "conf.py").is_file():
            found.append("doc")
        return list(dict.fromkeys(found))

    def walk(self) -> dict[str, DirSignals]:
        spec = load_gitignore_spec(self.root)
        signals: dict[str, DirSignals] = defaultdict(DirSignals)
        signals[""]
        for dirpath, dirnames, filenames in os.walk(self.root, topdown=True):
            current = Path(dirpath)
            rel_dir = current.relative_to(self.root).as_posix() if current != self.root else ""
            dirnames[:] = self.pruned(current, dirnames, spec)
            for name in filenames:
                rel = (current / name).relative_to(self.root).as_posix()
                if spec is None or not spec.match_file(rel):
                    self.record(signals[rel_dir], rel, name)
        return signals

    def pruned(
        self,
        current: Path,
        dirnames: list[str],
        spec: pathspec.PathSpec | None,
    ) -> list[str]:
        keep: list[str] = []
        for name in sorted(dirnames):
            if self.skip_dir(name):
                continue
            child = (current / name).relative_to(self.root).as_posix()
            if spec is not None and spec.match_file(child):
                continue
            if child.startswith(".shipgate/") or "/.shipgate/" in f"/{child}/":
                continue
            keep.append(name)
        return keep

    def skip_dir(self, name: str) -> bool:
        _ = self
        if name in SKIP_DIR_NAMES or name.startswith("."):
            return True
        return any(name.endswith(sfx) for sfx in SKIP_DIR_SUFFIXES)

    def record(self, sig: DirSignals, rel: str, name: str) -> None:
        _ = self
        lower = name.lower()
        if lower == "__init__.py":
            sig.has_init = True
        if lower == "conftest.py":
            sig.has_conftest = True
        if name.endswith(".py"):
            sig.py_files.append(rel)
            (sig.test_py_files if is_test_path(rel) else sig.prod_py_files).append(rel)
        elif Path(name).suffix.lower() in DOC_EXTENSIONS:
            sig.doc_files.append(rel)
