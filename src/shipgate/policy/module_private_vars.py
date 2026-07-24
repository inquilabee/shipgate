"""Module private-vars policy gate."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.files import (
    iter_python_files,
    scan_roots_from_config,
    should_skip_file,
)
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores

ASSIGN_PATTERN = re.compile(r"^_[^_][A-Za-z0-9_]*\s*[:=]")
DEF_PATTERN = re.compile(r"^(async\s+)?def\s+_[^_][A-Za-z0-9_]*\s*[\(:]")
CLASS_PATTERN = re.compile(r"^class\s+_[^_][A-Za-z0-9_]*\s*[\(:]")

RULE_IDS = {
    "assignment": "private-assignment",
    "function": "private-function",
    "class": "private-class",
}


def findings_for_file(rel: str, text: str) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if ASSIGN_PATTERN.match(line):
            findings.append(make_finding(rel, line_no, line, "assignment"))
        if DEF_PATTERN.match(line):
            findings.append(make_finding(rel, line_no, line, "function"))
        if CLASS_PATTERN.match(line):
            findings.append(make_finding(rel, line_no, line, "class"))
    return findings


def make_finding(rel: str, line_no: int, matched_line: str, label: str) -> PolicyFinding:
    return PolicyFinding(
        rule_id=RULE_IDS[label],
        message=f"{rel}:{line_no}:{matched_line}",
        location=FindingLocation(file=rel, line=line_no),
    )


class ModulePrivateVarsGate(PolicyGate):
    gate_id: ClassVar[str] = "module-private-vars"
    description: ClassVar[str] = "Module private-vars gate."

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        findings: list[PolicyFinding] = []
        for rel in iter_python_files(root, scan_roots_from_config(dict(config))):
            if should_skip_file(rel, allowlist, ignores):
                continue
            path = root / rel
            if not path.is_file():
                continue
            findings.extend(findings_for_file(rel, path.read_text(encoding="utf-8")))
        return findings


def main(argv: list[str] | None = None) -> int:
    return ModulePrivateVarsGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
