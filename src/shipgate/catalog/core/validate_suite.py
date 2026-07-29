"""Suite membership and cycle validation for catalog loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.ids import validate_id
from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog


def validate_suite_members(catalog: Catalog) -> None:
    for suite_id, suite in catalog.suites.items():
        try:
            validate_id(suite_id, kind="tool id")
        except ValueError as exc:
            raise CatalogError(str(exc)) from exc
        if not suite.members:
            raise CatalogError(f"suite {suite_id!r} has no members")
        for member in suite.members:
            if member not in catalog.tools and member not in catalog.suites:
                raise CatalogError(
                    f"suite {suite_id!r} references unknown member {member!r}",
                    hint='run "shipgate list tools" to see bundled tools',
                )
    for suite_id in catalog.suites:
        detect_suite_cycle(catalog, suite_id)


def detect_suite_cycle(catalog: Catalog, start: str) -> None:
    visited: set[str] = set()
    path: list[str] = []
    stack: list[tuple[str, int]] = [(start, 0)]

    while stack:
        node, member_index = stack[-1]
        if member_index == 0:
            if node in path:
                cycle = " -> ".join([*path, node])
                raise CatalogError(f"suite cycle detected: {cycle}")
            if node in visited or node not in catalog.suites:
                stack.pop()
                continue
            path.append(node)
        members = catalog.suites[node].members
        if member_index < len(members):
            stack[-1] = (node, member_index + 1)
            member = members[member_index]
            if member in catalog.suites:
                stack.append((member, 0))
            continue
        path.pop()
        visited.add(node)
        stack.pop()
