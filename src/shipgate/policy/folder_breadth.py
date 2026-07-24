"""Folder breadth policy gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.gates.scope_paths import scope_paths_from_env
from shipgate.policy.core.config import load_gate_mapping
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    import argparse
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores


@dataclass(frozen=True, slots=True)
class DirBreadthViolation:
    path: str
    count: int
    max_allowed: int


@dataclass(frozen=True, slots=True)
class FolderBreadthReport:
    max_allowed: int
    scan_roots: tuple[str, ...]
    extensions: tuple[str, ...]
    leaf_dirs_scanned: int
    leaf_dirs_over_max: int
    worst_leaf_dir: str
    worst_leaf_count: int
    violations: tuple[DirBreadthViolation, ...]

    def report_metadata(self) -> dict[str, int | str]:
        return {
            "leaf_dirs_scanned": self.leaf_dirs_scanned,
            "worst_leaf_dir": self.worst_leaf_dir,
            "worst_leaf_count": self.worst_leaf_count,
        }


SKIP_DIR_NAMES = frozenset({"__pycache__"})


class FolderBreadthGate(PolicyGate):
    gate_id: ClassVar[str] = "folder-breadth"
    description: ClassVar[str] = "Folder breadth gate."

    def __init__(self) -> None:
        self._report: FolderBreadthReport | None = None
        self._enforcing = True
        self._enforcing_override: bool | None = None

    @staticmethod
    def iter_scan_directories(base: Path) -> list[Path]:
        if not base.is_dir():
            return []
        directories = [base]
        for path in sorted(base.rglob("*")):
            if path.is_dir() and path.name not in SKIP_DIR_NAMES:
                directories.append(path)
        return directories

    @staticmethod
    def count_direct_files(directory: Path, extensions: tuple[str, ...]) -> int:
        count = 0
        for child in directory.iterdir():
            if not child.is_file():
                continue
            if child.name == "__init__.py":
                continue
            if child.suffix in extensions:
                count += 1
        return count

    @staticmethod
    def is_allowlisted(rel_posix: str, allowlist: set[str]) -> bool:
        normalized = rel_posix.rstrip("/")
        if normalized in allowlist:
            return True
        # Optional subtree exemption: `path/*` skips that directory and descendants.
        for entry in allowlist:
            if entry.endswith("/*"):
                prefix = entry[:-2].rstrip("/")
                if normalized == prefix or normalized.startswith(f"{prefix}/"):
                    return True
        return False

    @staticmethod
    def should_skip_directory(
        rel: str, allowlist: set[str], ignores: EffectiveIgnores | None
    ) -> bool:
        if FolderBreadthGate.is_allowlisted(rel, allowlist):
            return True
        return bool(ignores and ignores.is_ignored(rel))

    @staticmethod
    def breadth_violation(
        rel: str, file_count: int, max_allowed: int
    ) -> DirBreadthViolation | None:
        if file_count <= max_allowed:
            return None
        return DirBreadthViolation(path=rel, count=file_count, max_allowed=max_allowed)

    @staticmethod
    def directory_breadth_outcome(
        directory: Path,
        root: Path,
        *,
        max_allowed: int,
        extensions: tuple[str, ...],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> tuple[DirBreadthViolation | None, int, str] | None:
        rel = directory.relative_to(root).as_posix()
        if FolderBreadthGate.should_skip_directory(rel, allowlist, ignores):
            return None
        file_count = FolderBreadthGate.count_direct_files(directory, extensions)
        if file_count == 0:
            return None
        violation = FolderBreadthGate.breadth_violation(rel, file_count, max_allowed)
        return violation, file_count, rel

    @staticmethod
    def scan_root_breadth(
        root: Path,
        scan_root: str,
        *,
        max_allowed: int,
        extensions: tuple[str, ...],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
        worst_path: str,
        worst_count: int,
    ) -> tuple[int, str, int, list[DirBreadthViolation]]:
        violations: list[DirBreadthViolation] = []
        dirs_scanned = 0
        base = root / scan_root
        for directory in FolderBreadthGate.iter_scan_directories(base):
            outcome = FolderBreadthGate.directory_breadth_outcome(
                directory,
                root,
                max_allowed=max_allowed,
                extensions=extensions,
                allowlist=allowlist,
                ignores=ignores,
            )
            if outcome is None:
                continue
            violation, file_count, rel = outcome
            dirs_scanned += 1
            if file_count > worst_count:
                worst_count = file_count
                worst_path = rel
            if violation is not None:
                violations.append(violation)
        return dirs_scanned, worst_path, worst_count, violations

    @staticmethod
    def settings_from_config(
        config: dict[str, Any],
    ) -> tuple[int, tuple[str, ...], tuple[str, ...], bool]:
        max_allowed = int(config.get("max_allowed", 12))
        scan_roots = tuple(str(item) for item in config.get("scan_roots", ["."]))
        extensions_raw = config.get("extensions", [".py", ".md", ".yaml", ".sh"])
        extensions: list[str] = []
        for part in extensions_raw:
            stripped = str(part).strip()
            if not stripped:
                continue
            extensions.append(stripped if stripped.startswith(".") else f".{stripped}")
        strict = bool(config.get("strict", True))
        return max_allowed, scan_roots, tuple(extensions), strict

    @staticmethod
    def scan_folder_breadth(
        root: Path,
        *,
        max_allowed: int,
        scan_roots: tuple[str, ...],
        extensions: tuple[str, ...],
        allowlist: set[str],
        ignores: EffectiveIgnores | None = None,
    ) -> FolderBreadthReport:
        violations: list[DirBreadthViolation] = []
        dirs_scanned = 0
        worst_path = ""
        worst_count = 0

        scoped_roots = scope_paths_from_env()
        roots_to_scan = scoped_roots if scoped_roots else scan_roots

        for scan_root in roots_to_scan:
            scanned, worst_path, worst_count, root_violations = FolderBreadthGate.scan_root_breadth(
                root,
                scan_root,
                max_allowed=max_allowed,
                extensions=extensions,
                allowlist=allowlist,
                ignores=ignores,
                worst_path=worst_path,
                worst_count=worst_count,
            )
            dirs_scanned += scanned
            violations.extend(root_violations)

        violations.sort(key=lambda item: (-item.count, item.path))
        return FolderBreadthReport(
            max_allowed=max_allowed,
            scan_roots=scan_roots,
            extensions=extensions,
            leaf_dirs_scanned=dirs_scanned,
            leaf_dirs_over_max=len(violations),
            worst_leaf_dir=worst_path,
            worst_leaf_count=worst_count,
            violations=tuple(violations),
        )

    @staticmethod
    def findings_from_report(report: FolderBreadthReport) -> list[PolicyFinding]:
        findings: list[PolicyFinding] = []
        for violation in report.violations:
            findings.append(
                PolicyFinding(
                    rule_id="folder-breadth",
                    message=(
                        f"{violation.path} has {violation.count} sibling files "
                        f"(max {violation.max_allowed})"
                    ),
                    location=FindingLocation(file=violation.path),
                )
            )
        return findings

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--strict", action="store_true", default=None)
        parser.add_argument("--advisory", action="store_true", default=False)

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        max_allowed, scan_roots, extensions, config_strict = self.settings_from_config(dict(config))
        if self._enforcing_override is None:
            self._enforcing = config_strict
        else:
            self._enforcing = self._enforcing_override
        self._report = self.scan_folder_breadth(
            root,
            max_allowed=max_allowed,
            scan_roots=scan_roots,
            extensions=extensions,
            allowlist=allowlist,
            ignores=ignores,
        )
        return self.findings_from_report(self._report)

    def report_extra(self, findings: Sequence[PolicyFinding]) -> Mapping[str, object] | None:
        if self._report is None:
            return None
        return self._report.report_metadata()

    def fail_label(self, finding: PolicyFinding) -> str:
        return self.gate_id

    def emit_exit(self, findings: Sequence[PolicyFinding]) -> int:
        if not self._enforcing or not findings:
            return 0
        return super().emit_exit(findings)

    def main(self, argv: list[str] | None = None) -> int:
        args = self.parse_cli_args(argv)
        config = load_gate_mapping(args.config)
        if args.advisory:
            self._enforcing_override = False
        elif args.strict:
            self._enforcing_override = True
        return self.run(
            root=args.root.resolve(),
            config=config,
            report_path=args.report,
        )


def main(argv: list[str] | None = None) -> int:
    return FolderBreadthGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
