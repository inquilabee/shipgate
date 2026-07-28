"""Flag classes whose methods are exclusively ``@staticmethod``."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores


class StaticmethodSoupGate(PolicyGate):
    """Fail classes that define methods and every method is a staticmethod."""

    gate_id: ClassVar[str] = "staticmethod-soup"
    description: ClassVar[str] = "Staticmethod-soup gate."

    @staticmethod
    def parse_python(source: str, *, filename: str = "<unknown>") -> ast.AST | None:
        try:
            return ast.parse(source, filename=filename)
        except SyntaxError:
            return None

    @staticmethod
    def is_staticmethod(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr == "staticmethod":
                return True
        return False

    @staticmethod
    def class_methods(node: ast.ClassDef) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        return [
            child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    @staticmethod
    def is_soup(methods: Sequence[ast.FunctionDef | ast.AsyncFunctionDef]) -> bool:
        return (
            all(StaticmethodSoupGate.is_staticmethod(method) for method in methods)
            if methods
            else False
        )

    @staticmethod
    def findings_for_source(rel: str, source: str) -> list[PolicyFinding]:
        tree = StaticmethodSoupGate.parse_python(source, filename=rel)
        if tree is None or not isinstance(tree, ast.Module):
            return []
        findings: list[PolicyFinding] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = StaticmethodSoupGate.class_methods(node)
            if methods and StaticmethodSoupGate.is_soup(methods):
                count = sum(1 for _ in methods)
                findings.append(
                    PolicyFinding(
                        rule_id="staticmethod-soup",
                        message=(
                            f"class {node.name} in {rel} has {count} method(s), "
                            "all @staticmethod; prefer module functions or real methods"
                        ),
                        location=FindingLocation(file=rel, line=node.lineno),
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
        findings: list[PolicyFinding] = []
        for rel, path in self.iter_scoped_python_files(root, config, allowlist, ignores):
            findings.extend(
                StaticmethodSoupGate.findings_for_source(
                    rel,
                    path.read_text(encoding="utf-8"),
                )
            )
        return findings


def main(argv: list[str] | None = None) -> int:
    return StaticmethodSoupGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
