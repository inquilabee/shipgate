"""Major.minor Python specifiers for catalog install.requires_python."""

from __future__ import annotations

import sys

OPERATORS = (">=", "<=", ">", "<")


class PythonVersionSpec:
    """Parse and match comma-separated ``>=3.11,<3.14`` style bounds."""

    def __init__(self, spec: str) -> None:
        self.spec = spec.strip()
        if not self.spec:
            raise ValueError("specifier must not be empty")
        clauses = [self._parse_clause(part.strip()) for part in self.spec.split(",")]
        self.clauses = tuple(clauses)

    @classmethod
    def parse(cls, spec: str) -> PythonVersionSpec:
        return cls(spec)

    def matches(self, version: tuple[int, int]) -> bool:
        return all(self._clause_matches(op, bound, version) for op, bound in self.clauses)

    def unsupported_message(self, name: str, version: tuple[int, int]) -> str | None:
        if self.matches(version):
            return None
        py = f"{version[0]}.{version[1]}"
        return f"{name} does not support Python {py} (requires_python: {self.spec})"

    def _parse_clause(self, clause: str) -> tuple[str, tuple[int, int]]:
        if not clause:
            raise self._invalid_spec()
        for operator in OPERATORS:
            if not clause.startswith(operator):
                continue
            rest = clause.removeprefix(operator).strip()
            parts = rest.split(".")
            if len(parts) != 2 or any(not part.isdigit() for part in parts):
                raise self._invalid_spec()
            return operator, (int(parts[0]), int(parts[1]))
        raise self._invalid_spec()

    def _invalid_spec(self) -> ValueError:
        return ValueError(f"invalid requires_python specifier: {self.spec!r}")

    @staticmethod
    def _clause_matches(operator: str, bound: tuple[int, int], version: tuple[int, int]) -> bool:
        comparisons = {
            ">=": version >= bound,
            "<=": version <= bound,
            ">": version > bound,
            "<": version < bound,
        }
        return comparisons[operator]


def host_python_minor() -> tuple[int, int]:
    return sys.version_info[0], sys.version_info[1]
