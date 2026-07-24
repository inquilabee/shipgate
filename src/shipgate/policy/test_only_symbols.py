"""Flag production classes/methods that are only referenced from tests."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.files import (
    iter_python_files,
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


@dataclass(frozen=True, slots=True)
class SymbolDefinition:
    kind: str
    name: str
    qualname: str
    file: str
    line: int


@dataclass(frozen=True, slots=True)
class SymbolIndex:
    definitions: tuple[SymbolDefinition, ...]
    production_refs: frozenset[str]
    test_refs: frozenset[str]


class DefinitionCollector(ast.NodeVisitor):
    """Collect top-level classes, functions, and methods from production modules."""

    def __init__(self, file: str) -> None:
        self.file = file
        self.definitions: list[SymbolDefinition] = []
        self._class_stack: list[str] = []

    @staticmethod
    def is_dunder(name: str) -> bool:
        return name.startswith("__") and name.endswith("__")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = ".".join([*self._class_stack, node.name])
        self.definitions.append(
            SymbolDefinition(
                kind="class",
                name=node.name,
                qualname=qualname,
                file=self.file,
                line=node.lineno,
            )
        )
        self._class_stack.append(node.name)
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._add_method(child)
            elif isinstance(child, ast.ClassDef):
                self.visit_ClassDef(child)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._add_module_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._add_module_function(node)

    def _add_module_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self._class_stack:
            return
        if self.is_dunder(node.name):
            return
        self.definitions.append(
            SymbolDefinition(
                kind="function",
                name=node.name,
                qualname=node.name,
                file=self.file,
                line=node.lineno,
            )
        )

    def _add_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self.is_dunder(node.name):
            return
        qualname = ".".join([*self._class_stack, node.name])
        self.definitions.append(
            SymbolDefinition(
                kind="method",
                name=node.name,
                qualname=qualname,
                file=self.file,
                line=node.lineno,
            )
        )


class ReferenceCollector(ast.NodeVisitor):
    """Collect loaded names, attribute names, and import bindings."""

    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.names.add(node.attr)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue
            self.names.add(alias.name)
            if alias.asname:
                self.names.add(alias.asname)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname:
                self.names.add(alias.asname)
            else:
                self.names.add(alias.name.split(".", 1)[0])


class TestOnlySymbolsGate(PolicyGate):
    gate_id: ClassVar[str] = "test-only-symbols"
    description: ClassVar[str] = "Test-only symbols gate."

    @staticmethod
    def collect_definitions(rel: str, tree: ast.AST) -> list[SymbolDefinition]:
        collector = DefinitionCollector(rel)
        collector.visit(tree)
        return collector.definitions

    @staticmethod
    def collect_references(tree: ast.AST) -> set[str]:
        collector = ReferenceCollector()
        collector.visit(tree)
        return collector.names

    @staticmethod
    def parse_python(path: Path) -> ast.AST | None:
        try:
            return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            return None

    @staticmethod
    def should_skip_symbol(rel: str, qualname: str, allowlist: set[str]) -> bool:
        if rel.rstrip("/") in allowlist:
            return True
        return f"{rel.rstrip('/')}:{qualname}" in allowlist

    @staticmethod
    def index_python_files(
        root: Path,
        files: Sequence[str],
    ) -> SymbolIndex:
        definitions: list[SymbolDefinition] = []
        production_refs: set[str] = set()
        test_refs: set[str] = set()
        for rel in files:
            path = root / rel
            if not path.is_file():
                continue
            tree = TestOnlySymbolsGate.parse_python(path)
            if tree is None:
                continue
            if is_test_path(rel):
                test_refs |= TestOnlySymbolsGate.collect_references(tree)
                continue
            definitions.extend(TestOnlySymbolsGate.collect_definitions(rel, tree))
            production_refs |= TestOnlySymbolsGate.collect_references(tree)
        return SymbolIndex(
            definitions=tuple(definitions),
            production_refs=frozenset(production_refs),
            test_refs=frozenset(test_refs),
        )

    @staticmethod
    def is_test_only_symbol(symbol: SymbolDefinition, index: SymbolIndex) -> bool:
        if symbol.name not in index.test_refs:
            return False
        return symbol.name not in index.production_refs

    @staticmethod
    def finding_for_symbol(symbol: SymbolDefinition) -> PolicyFinding:
        return PolicyFinding(
            rule_id="test-only-symbol",
            message=(
                f"{symbol.kind} {symbol.qualname} in {symbol.file} is only referenced from tests"
            ),
            location=FindingLocation(file=symbol.file, line=symbol.line),
        )

    @staticmethod
    def finding_sort_key(item: PolicyFinding) -> tuple[str, int]:
        location = item.location
        if location is None:
            return ("", 0)
        return (location.file, location.line or 0)

    @staticmethod
    def findings_from_index(index: SymbolIndex, allowlist: set[str]) -> list[PolicyFinding]:
        findings = [
            TestOnlySymbolsGate.finding_for_symbol(symbol)
            for symbol in index.definitions
            if not TestOnlySymbolsGate.should_skip_symbol(symbol.file, symbol.qualname, allowlist)
            and TestOnlySymbolsGate.is_test_only_symbol(symbol, index)
        ]
        findings.sort(key=TestOnlySymbolsGate.finding_sort_key)
        return findings

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        files = [
            rel
            for rel in iter_python_files(root, scan_roots_from_config(dict(config)))
            if not should_skip_file(rel, set(), ignores)
        ]
        return self.findings_from_index(self.index_python_files(root, files), allowlist)


def main(argv: list[str] | None = None) -> int:
    return TestOnlySymbolsGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
