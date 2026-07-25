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
from shipgate.policy.core.files import (
    iter_python_files,
    scan_roots_from_config,
    should_skip_file,
)
from shipgate.policy.core.finding import PolicyFinding
from shipgate.policy.core.report import write_findings_report

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

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

    def report_extra(  # ruff:ignore[no-self-use]
        self,
        findings: Sequence[PolicyFinding],
    ) -> Mapping[str, object] | None:
        _ = findings
        return None

    def fail_label(self, finding: PolicyFinding) -> str:  # ruff:ignore[no-self-use]
        return finding.rule_id

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:  # ruff:ignore[no-self-use]
        """Hook for gate-specific CLI flags."""
        _ = parser

    def resolve_allowlist(  # ruff:ignore[no-self-use]
        self,
        root: Path,
        config: Mapping[str, Any],
    ) -> set[str]:
        return load_allowlist_paths(resolve_config_allowlist(root, dict(config)))

    def iter_scoped_python_files(  # ruff:ignore[no-self-use]
        self,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Iterator[tuple[str, Path]]:
        for rel in iter_python_files(root, scan_roots_from_config(dict(config))):
            if should_skip_file(rel, allowlist, ignores):
                continue
            path = root / rel
            if path.is_file():
                yield rel, path

    def parse_cli_args(self, argv: list[str] | None = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description=self.description)
        parser.add_argument("--root", type=Path, default=Path.cwd())
        parser.add_argument("--config", type=Path, required=True)
        parser.add_argument("--report", type=Path, default=None)
        self.configure_parser(parser)
        return parser.parse_args(argv)

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
        args = self.parse_cli_args(argv)
        return self.run(
            root=args.root.resolve(),
            config=load_gate_mapping(args.config),
            report_path=args.report,
        )
