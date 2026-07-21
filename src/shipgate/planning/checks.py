"""Check helpers."""

from shipgate.domain.catalog import Catalog
from shipgate.domain.project import ProjectConfig
from shipgate.planning.suites import expand_suite


def list_catalog_checks(catalog: Catalog) -> list[str]:
    return sorted(catalog.tools.keys())


def list_project_checks(project: ProjectConfig, catalog: Catalog) -> list[str]:
    if project.check_bindings:
        return sorted(binding.runnable for binding in project.check_bindings)
    if project.checks:
        expanded: list[str] = []
        seen: set[str] = set()
        for check_name in project.checks:
            for tool_id in expand_suite(check_name, catalog):
                if tool_id not in seen:
                    seen.add(tool_id)
                    expanded.append(tool_id)
        return expanded
    return list_catalog_checks(catalog)
