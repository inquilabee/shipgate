"""Project catalog sync helpers."""

from __future__ import annotations

from pathlib import Path

from shipgate.gates.paths import bundled_root_path
from shipgate.project.config_setup import scaffold_file_if_missing

CATALOG_SECTIONS = ("suites", "workflows", "capabilities")


def bundled_catalog_dir() -> Path:
    return bundled_root_path() / "catalog"


def sync_catalog(project_root: Path) -> list[Path]:
    """Copy missing bundled catalog files into .shipgate/catalog/."""
    root = project_root.resolve()
    bundled = bundled_catalog_dir()
    created: list[Path] = []

    tools_src = bundled / "tools"
    if tools_src.is_dir():
        for src in sorted(tools_src.glob("*.yaml")):
            result = scaffold_file_if_missing(
                root,
                Path(".shipgate/catalog/tools") / src.name,
                bundled_template=src,
            )
            if result is not None:
                created.append(result)

    for section in CATALOG_SECTIONS:
        src = bundled / f"{section}.yaml"
        if not src.is_file():
            continue
        result = scaffold_file_if_missing(
            root,
            Path(f".shipgate/catalog/{section}.yaml"),
            bundled_template=src,
        )
        if result is not None:
            created.append(result)

    return created
