"""Map layout python dirs to importable package names."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.project.layout.engine import LayoutEngine

if TYPE_CHECKING:
    from pathlib import Path


def detect_importable_packages(project_root: Path) -> tuple[str, ...]:
    """Importable package names from layout detection (src or flat)."""
    return RootPackageDetector(project_root).packages()


def detect_importable_root_package(project_root: Path) -> str | None:
    """First importable package name for import-linter / deptry scaffolding."""
    packages = detect_importable_packages(project_root)
    return packages[0] if packages else None


def has_src_layout_package(project_root: Path) -> bool:
    """True when ``src/<pkg>/__init__.py`` exists (managed PYTHONPATH=src)."""
    return RootPackageDetector(project_root).from_src_layout() is not None


class RootPackageDetector:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()

    def packages(self) -> tuple[str, ...]:
        names: list[str] = []
        for rel in LayoutEngine(self.root).detect().python_dirs:
            names.extend(self._names_for_python_dir(rel))
        return tuple(sorted(set(names)))

    def from_src_layout(self) -> str | None:
        found = self._packages_under(self.root / "src")
        return found[0] if found else None

    def _names_for_python_dir(self, rel: str) -> tuple[str, ...]:
        if rel == "src":
            return self._packages_under(self.root / "src")
        path = self.root / rel
        return (path.name,) if (path / "__init__.py").is_file() else ()

    @staticmethod
    def _packages_under(parent: Path) -> tuple[str, ...]:
        return (
            tuple(
                sorted(
                    path.name
                    for path in parent.iterdir()
                    if path.is_dir()
                    and not path.name.startswith(".")
                    and (path / "__init__.py").is_file()
                )
            )
            if parent.is_dir()
            else ()
        )
