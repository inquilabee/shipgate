"""Flag repeated string literals that should be named constants."""

from __future__ import annotations

import ast
from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.files import (
    iter_python_files,
    path_is_allowlisted,
    scan_roots_from_config,
    should_skip_file,
)
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate
from shipgate.policy.core.test_paths import is_test_path

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores

BUILTIN_EXEMPT = frozenset(
    {
        "",
        "utf-8",
        "ascii",
        "strict",
        "ignore",
        "replace",
        "surrogateescape",
    }
)


class RepeatedStringsGate(PolicyGate):
    gate_id: ClassVar[str] = "repeated-strings"
    description: ClassVar[str] = "Repeated string constants gate."

    @staticmethod
    def parse_python(source: str, *, filename: str = "<unknown>") -> ast.AST | None:
        try:
            return ast.parse(source, filename=filename)
        except SyntaxError:
            return None

    @staticmethod
    def docstring_nodes(tree: ast.AST) -> set[ast.AST]:
        nodes: set[ast.AST] = set()
        for parent in ast.walk(tree):
            body = getattr(parent, "body", None)
            if not isinstance(body, list) or not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                nodes.add(first.value)
        return nodes

    @staticmethod
    def collect_string_literals(source: str) -> list[str]:
        tree = RepeatedStringsGate.parse_python(source)
        if tree is None:
            return []
        docs = RepeatedStringsGate.docstring_nodes(tree)
        values: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if node in docs:
                continue
            values.append(node.value)
        return values

    @staticmethod
    def first_line_for_string(source: str, value: str) -> int:
        tree = RepeatedStringsGate.parse_python(source)
        if tree is None:
            return 1
        docs = RepeatedStringsGate.docstring_nodes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or node.value != value:
                continue
            if node in docs:
                continue
            return int(getattr(node, "lineno", 1) or 1)
        return 1

    @staticmethod
    def should_consider_string(value: str, *, min_length: int, exempt_strings: set[str]) -> bool:
        if len(value) < min_length:
            return False
        if value in BUILTIN_EXEMPT or value in exempt_strings:
            return False
        if value.isidentifier():
            return False
        return not value.isspace()

    @staticmethod
    def findings_for_file(
        rel: str,
        source: str,
        *,
        min_occurrences: int,
        min_length: int,
        exempt_strings: set[str],
        allowlist: set[str],
    ) -> list[PolicyFinding]:
        if path_is_allowlisted(rel, allowlist):
            return []
        counts = Counter(RepeatedStringsGate.collect_string_literals(source))
        findings: list[PolicyFinding] = []
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            if count < min_occurrences:
                continue
            if not RepeatedStringsGate.should_consider_string(
                value, min_length=min_length, exempt_strings=exempt_strings
            ):
                continue
            if f"string:{value}" in allowlist:
                continue
            findings.append(
                PolicyFinding(
                    rule_id="repeated-string",
                    message=(f"{rel} repeats {value!r} {count} times; extract a named constant"),
                    location=FindingLocation(
                        file=rel,
                        line=RepeatedStringsGate.first_line_for_string(source, value),
                    ),
                )
            )
        return findings

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        min_occurrences = int(config.get("min_occurrences", 3))
        min_length = int(config.get("min_length", 8))
        include_tests = bool(config.get("include_tests", False))
        exempt_raw = config.get("exempt_strings", [])
        exempt_strings: set[str] = set()
        if isinstance(exempt_raw, list | tuple):
            exempt_strings = {str(item) for item in exempt_raw}
        findings: list[PolicyFinding] = []
        for rel in iter_python_files(root, scan_roots_from_config(dict(config))):
            if not include_tests and is_test_path(rel):
                continue
            if should_skip_file(rel, allowlist, ignores):
                continue
            path = root / rel
            if not path.is_file():
                continue
            findings.extend(
                self.findings_for_file(
                    rel,
                    path.read_text(encoding="utf-8"),
                    min_occurrences=min_occurrences,
                    min_length=min_length,
                    exempt_strings=exempt_strings,
                    allowlist=allowlist,
                )
            )
        return findings


def main(argv: list[str] | None = None) -> int:
    return RepeatedStringsGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
