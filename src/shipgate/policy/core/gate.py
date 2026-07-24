"""Abstract base for bundled Python policy gates."""

from __future__ import annotations

import argparse
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.gates.ignore import ignores_from_env
from shipgate.policy.core.config import (
    load_allowlist_paths,
    load_gate_mapping,
    resolve_config_allowlist,
)
from shipgate.policy.core.finding import PolicyFinding
from shipgate.policy.core.report import write_findings_report

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from shipgate.gates.ignore import EffectiveIgnores


class PolicyGate(ABC):
    """Lifecycle owner for one policy check: config → scan → report → exit."""

    gate_id: ClassVar[str]
    description: ClassVar[str] = "Policy gate."

    @abstractmethod
    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        """Return findings for the current project tree."""

    def report_extra(self, findings: Sequence[PolicyFinding]) -> Mapping[str, object] | None:
        return None

    def fail_label(self, finding: PolicyFinding) -> str:
        return finding.rule_id

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        """Hook for gate-specific CLI flags."""
        _ = parser

    def resolve_allowlist(self, root: Path, config: Mapping[str, Any]) -> set[str]:
        return load_allowlist_paths(resolve_config_allowlist(root, dict(config)))

    def run(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        report_path: Path | None,
        ignores: EffectiveIgnores | None = None,
    ) -> int:
        effective_ignores = ignores if ignores is not None else ignores_from_env(root)
        findings = list[PolicyFinding](
            self.collect_findings(
                root=root,
                config=config,
                allowlist=self.resolve_allowlist(root, config),
                ignores=effective_ignores,
            )
        )
        write_findings_report(
            findings,
            report_path,
            extra=self.report_extra(findings),
        )
        return self.emit_exit(findings)

    def emit_exit(self, findings: Sequence[PolicyFinding]) -> int:
        if not findings:
            return 0
        for finding in findings:
            print(
                f"FAIL {self.fail_label(finding)}: {finding.message}",
                file=sys.stderr,
            )
        return 1

    def main(self, argv: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("--root", type=Path, default=Path.cwd())
        parser.add_argument("--config", type=Path, required=True)
        parser.add_argument("--report", type=Path, default=None)
        self.configure_parser(parser)
        args = parser.parse_args(argv)
        return self.run(
            root=args.root.resolve(),
            config=load_gate_mapping(args.config),
            report_path=args.report,
        )
