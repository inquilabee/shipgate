"""Folder breadth policy gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.gates.scope_paths import scope_paths_from_env
from shipgate.planning.utils.gitignore import ignored_path_part
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


class FolderBreadthGate(PolicyGate):
    gate_id: ClassVar[str] = "folder-breadth"
    description: ClassVar[str] = "Folder breadth gate."

    def __init__(self) -> None:
        self._report: FolderBreadthReport | None = None
        self._enforcing = True
        self._enforcing_override: bool | None = None
        self._root: Path | None = None
        self._max_allowed = 12
        self._scan_roots: tuple[str, ...] = (".",)
        self._extensions: tuple[str, ...] = (".py", ".md", ".yaml", ".sh")
        self._allowlist: set[str] = set()
        self._ignores: EffectiveIgnores | None = None

    def configure_parser(self, parser: argparse.ArgumentParser) -> None:  # ruff:ignore[no-self-use]
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
        max_allowed, scan_roots, extensions, config_strict = self._settings_from_config(
            dict(config)
        )
        self._enforcing = (
            config_strict if self._enforcing_override is None else self._enforcing_override
        )
        self._root = root
        self._max_allowed = max_allowed
        self._scan_roots = scan_roots
        self._extensions = extensions
        self._allowlist = allowlist
        self._ignores = ignores
        self._report = self._scan_folder_breadth()
        return self._findings_from_report(self._report)

    def report_extra(self, findings: Sequence[PolicyFinding]) -> Mapping[str, object] | None:
        _ = findings
        return None if self._report is None else self._report.report_metadata()

    def fail_label(self, finding: PolicyFinding) -> str:
        _ = finding
        return self.gate_id

    def emit_exit(self, findings: Sequence[PolicyFinding]) -> int:
        return 0 if not self._enforcing or not findings else super().emit_exit(findings)

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

    @staticmethod
    def _settings_from_config(
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
        strict = config.get("strict", True)
        return max_allowed, scan_roots, tuple(extensions), strict

    def _scan_folder_breadth(self) -> FolderBreadthReport:
        if self._root is None:
            msg = "scan root is not bound"
            raise RuntimeError(msg)
        violations: list[DirBreadthViolation] = []
        dirs_scanned = 0
        worst_path = ""
        worst_count = 0

        scoped_roots = scope_paths_from_env()
        roots_to_scan = scoped_roots or self._scan_roots

        for scan_root in roots_to_scan:
            scanned, worst_path, worst_count, root_violations = self._scan_root_breadth(
                scan_root,
                worst_path=worst_path,
                worst_count=worst_count,
            )
            dirs_scanned += scanned
            violations.extend(root_violations)

        violations.sort(key=lambda item: (-item.count, item.path))
        return FolderBreadthReport(
            max_allowed=self._max_allowed,
            scan_roots=self._scan_roots,
            extensions=self._extensions,
            leaf_dirs_scanned=dirs_scanned,
            leaf_dirs_over_max=len(violations),
            worst_leaf_dir=worst_path,
            worst_leaf_count=worst_count,
            violations=tuple(violations),
        )

    def _scan_root_breadth(
        self,
        scan_root: str,
        *,
        worst_path: str,
        worst_count: int,
    ) -> tuple[int, str, int, list[DirBreadthViolation]]:
        if self._root is None:
            return 0, worst_path, worst_count, []
        violations: list[DirBreadthViolation] = []
        dirs_scanned = 0
        base = self._root / scan_root
        for directory in self._scan_directories(base):
            outcome = self._directory_breadth_outcome(directory)
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

    def _directory_breadth_outcome(
        self, directory: Path
    ) -> tuple[DirBreadthViolation | None, int, str] | None:
        if self._root is None:
            return None
        rel = directory.relative_to(self._root).as_posix()
        if self._should_skip_directory(rel):
            return None
        file_count = self._count_direct_files(directory)
        if file_count == 0:
            return None
        violation = self._breadth_violation(rel, file_count)
        return violation, file_count, rel

    def _should_skip_directory(self, rel: str) -> bool:
        return (
            True
            if self._is_allowlisted(rel)
            else (self._ignores.is_ignored(rel) if self._ignores is not None else False)
        )

    def _is_allowlisted(self, rel_posix: str) -> bool:
        normalized = rel_posix.rstrip("/")
        if normalized in self._allowlist:
            return True
        for entry in self._allowlist:
            if entry.endswith("/*"):
                prefix = entry[:-2].rstrip("/")
                if normalized == prefix or normalized.startswith(f"{prefix}/"):
                    return True
        return False

    def _breadth_violation(self, rel: str, file_count: int) -> DirBreadthViolation | None:
        return (
            None
            if file_count <= self._max_allowed
            else DirBreadthViolation(
                path=rel,
                count=file_count,
                max_allowed=self._max_allowed,
            )
        )

    def _scan_directories(self, base: Path) -> list[Path]:
        if not base.is_dir():
            return []
        found: list[Path] = []
        pending = [base]
        while pending:
            current = pending.pop()
            found.append(current)
            pending.extend(self._walkable_children(current))
        return found

    def _walkable_children(self, directory: Path) -> list[Path]:
        return sorted(
            child
            for child in directory.iterdir()
            if child.is_dir() and not self._should_prune_walk(child)
        )

    def _should_prune_walk(self, directory: Path) -> bool:
        if self._root is None:
            return True
        rel = directory.relative_to(self._root).as_posix()
        return ignored_path_part(rel) if self._ignores is None else self._ignores.is_ignored(rel)

    def _count_direct_files(self, directory: Path) -> int:
        count = 0
        for child in directory.iterdir():
            if not child.is_file():
                continue
            if child.name == "__init__.py":
                continue
            if child.suffix in self._extensions:
                count += 1
        return count

    @staticmethod
    def _findings_from_report(report: FolderBreadthReport) -> list[PolicyFinding]:
        findings: list[PolicyFinding] = [
            PolicyFinding(
                rule_id="folder-breadth",
                message=(
                    f"{violation.path} has {violation.count} sibling files "
                    f"(max {violation.max_allowed})"
                ),
                location=FindingLocation(file=violation.path),
            )
            for violation in report.violations
        ]
        return findings


def main(argv: list[str] | None = None) -> int:
    return FolderBreadthGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
