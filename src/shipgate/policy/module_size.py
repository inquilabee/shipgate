"""Module size policy gate."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.policy.core.files import (
    iter_python_files,
    should_skip_file,
)
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores

BLANK_LINE = re.compile(r"^\s*$")
GATE_ID = "module-size"

__all__ = [
    "ModuleSizeGate",
    "iter_python_files",
    "main",
    "should_skip_file",
]


class ModuleSizeGate(PolicyGate):
    gate_id: ClassVar[str] = GATE_ID
    description: ClassVar[str] = "Module size gate."

    @staticmethod
    def count_non_blank_lines(text: str) -> int:
        return sum(1 for line in text.splitlines() if not BLANK_LINE.match(line))

    @staticmethod
    def check_file_size(
        rel: str,
        loc: int,
        *,
        module_max: int,
        portfolio_max: int,
    ) -> PolicyFinding | None:
        if loc > module_max:
            return PolicyFinding(
                rule_id=GATE_ID,
                message=f"{rel} has {loc} lines (module cap {module_max})",
                location=FindingLocation(file=rel, line=1),
            )
        if loc > portfolio_max:
            return PolicyFinding(
                rule_id=GATE_ID,
                message=f"{rel} has {loc} lines (portfolio cap {portfolio_max})",
                location=FindingLocation(file=rel, line=1),
            )
        return None

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        portfolio_max = int(config.get("portfolio_max_lines", 1000))
        module_max = int(config.get("module_max_lines", 500))
        findings: list[PolicyFinding] = []
        for rel, path in self.iter_scoped_python_files(root, config, allowlist, ignores):
            loc = self.count_non_blank_lines(path.read_text(encoding="utf-8"))
            finding = self.check_file_size(
                rel, loc, module_max=module_max, portfolio_max=portfolio_max
            )
            if finding is not None:
                findings.append(finding)
        return findings

    def fail_label(self, finding: PolicyFinding) -> str:
        return self.gate_id


def main(argv: list[str] | None = None) -> int:
    return ModuleSizeGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
