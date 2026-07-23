"""Compatibility re-export — prefer shipgate.project.python."""

from shipgate.project.python import (
    ProjectPythonResolver,
    discover_and_persist_project_python,
    discover_project_python,
    persist_project_python,
    read_cached_project_python,
    resolve_cached_project_python,
    validate_project_python,
)

__all__ = [
    "ProjectPythonResolver",
    "discover_and_persist_project_python",
    "discover_project_python",
    "persist_project_python",
    "read_cached_project_python",
    "resolve_cached_project_python",
    "validate_project_python",
]
