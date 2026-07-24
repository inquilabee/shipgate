"""Flag module-level helpers that are only used inside one class."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.files import symbol_is_allowlisted
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores


@dataclass(frozen=True, slots=True)
class ModuleFunction:
    name: str
    line: int
    first_arg: str | None


@dataclass(frozen=True, slots=True)
class NameReference:
    name: str
    class_name: str | None


class ReferenceCollector(ast.NodeVisitor):
    """Collect name loads with the enclosing class, if any."""

    def __init__(self) -> None:
        self.refs: list[NameReference] = []
        self._class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            class_name = self._class_stack[-1] if self._class_stack else None
            self.refs.append(NameReference(name=node.id, class_name=class_name))


class ClassLocalFunctionsGate(PolicyGate):
    gate_id: ClassVar[str] = "class-local-functions"
    description: ClassVar[str] = "Class-local functions gate."

    @staticmethod
    def parse_python(source: str, *, filename: str = "<unknown>") -> ast.AST | None:
        try:
            return ast.parse(source, filename=filename)
        except SyntaxError:
            return None

    @staticmethod
    def is_dunder(name: str) -> bool:
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def is_private(name: str) -> bool:
        return name.startswith("_") and not ClassLocalFunctionsGate.is_dunder(name)

    @staticmethod
    def module_functions(tree: ast.AST, *, private_only: bool) -> list[ModuleFunction]:
        if not isinstance(tree, ast.Module):
            return []
        functions: list[ModuleFunction] = []
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if ClassLocalFunctionsGate.is_dunder(node.name) or node.name == "main":
                continue
            if private_only and not ClassLocalFunctionsGate.is_private(node.name):
                continue
            first_arg = None
            if node.args.args:
                first_arg = node.args.args[0].arg
            functions.append(ModuleFunction(name=node.name, line=node.lineno, first_arg=first_arg))
        return functions

    @staticmethod
    def decorator_kind(function: ModuleFunction) -> str:
        if function.first_arg == "cls":
            return "classmethod"
        return "staticmethod"

    @staticmethod
    def class_local_finding(
        rel: str,
        function: ModuleFunction,
        class_name: str,
    ) -> PolicyFinding:
        kind = ClassLocalFunctionsGate.decorator_kind(function)
        return PolicyFinding(
            rule_id="class-local-function",
            message=(
                f"function {function.name} in {rel} is only used by class "
                f"{class_name}; move it to @{kind}"
            ),
            location=FindingLocation(file=rel, line=function.line),
        )

    @staticmethod
    def sole_class_name(refs: Sequence[NameReference]) -> str | None:
        class_names = {ref.class_name for ref in refs}
        if None in class_names or len(class_names) != 1:
            return None
        return next(iter(class_names))

    @staticmethod
    def findings_for_source(
        rel: str,
        source: str,
        allowlist: set[str],
        *,
        private_only: bool,
    ) -> list[PolicyFinding]:
        tree = ClassLocalFunctionsGate.parse_python(source, filename=rel)
        if tree is None:
            return []
        functions = ClassLocalFunctionsGate.module_functions(tree, private_only=private_only)
        if not functions:
            return []
        collector = ReferenceCollector()
        collector.visit(tree)
        findings: list[PolicyFinding] = []
        for function in functions:
            if symbol_is_allowlisted(rel, function.name, allowlist):
                continue
            refs = [ref for ref in collector.refs if ref.name == function.name]
            if not refs:
                continue
            class_name = ClassLocalFunctionsGate.sole_class_name(refs)
            if class_name is None:
                continue
            findings.append(ClassLocalFunctionsGate.class_local_finding(rel, function, class_name))
        return findings

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        private_only = bool(config.get("private_only", False))
        findings: list[PolicyFinding] = []
        for rel, path in self.iter_scoped_python_files(root, config, allowlist, ignores):
            findings.extend(
                self.findings_for_source(
                    rel,
                    path.read_text(encoding="utf-8"),
                    allowlist,
                    private_only=private_only,
                )
            )
        return findings


def main(argv: list[str] | None = None) -> int:
    return ClassLocalFunctionsGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
