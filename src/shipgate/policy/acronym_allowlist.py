"""Documented-acronym policy gate."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import yaml

from shipgate.gates.scope_paths import scope_paths_from_env
from shipgate.policy.core.finding import FindingLocation, PolicyFinding
from shipgate.policy.core.gate import PolicyGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from shipgate.gates.ignore import EffectiveIgnores

ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
FENCED_CODE_BLOCK_RE = re.compile(r"(`{3,})[\s\S]*?\1", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]+`")

BUILTIN_EXEMPT: frozenset[str] = frozenset(
    {
        "ADR",
        "AGENTS",
        "API",
        "ASGI",
        "AST",
        "CI",
        "CLI",
        "CORS",
        "CPU",
        "CRUD",
        "CSRF",
        "CSS",
        "CSV",
        "DTO",
        "DRY",
        "FAIL",
        "GET",
        "GPL",
        "HEAD",
        "HTML",
        "HTTP",
        "HTTPS",
        "IDE",
        "ID",
        "IO",
        "IP",
        "ISO",
        "JSON",
        "JWT",
        "LOC",
        "NO",
        "NOT",
        "OK",
        "ON",
        "PATCH",
        "PATH",
        "PDF",
        "POST",
        "PUT",
        "README",
        "REST",
        "RUN",
        "SDD",
        "SHA",
        "SQL",
        "SSH",
        "SVG",
        "TBD",
        "TODO",
        "TS",
        "URL",
        "UTC",
        "UUID",
        "VM",
        "WCAG",
        "XML",
        "YAML",
    }
)


@dataclass(frozen=True, slots=True)
class AcronymViolation:
    path: str
    line: int
    token: str


class AcronymAllowlistGate(PolicyGate):
    gate_id: ClassVar[str] = "acronym-allowlist"
    description: ClassVar[str] = "Documented-acronym gate."

    def __init__(self) -> None:
        self._root: Path | None = None
        self._allowlisted: set[str] = set()
        self._scan_roots: tuple[str, ...] = (".",)
        self._ignores: EffectiveIgnores | None = None

    @staticmethod
    def strip_markdown_code(text: str) -> str:
        without_fences = FENCED_CODE_BLOCK_RE.sub("", text)
        return INLINE_CODE_RE.sub("", without_fences)

    def resolve_allowlist(self, root: Path, config: Mapping[str, Any]) -> set[str]:
        # Token allowlists are loaded inside collect_findings.
        return set()

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        scan_roots, allowlist_path = self._settings_from_config(dict(config))
        self._root = root
        self._scan_roots = scan_roots
        self._ignores = ignores
        self._allowlisted = self._load_allowlist(self._require_allowlist_path(allowlist_path))
        return self._findings_from_violations(self._scan_paths())

    def fail_label(self, finding: PolicyFinding) -> str:
        return "acronym"

    def emit_exit(self, findings: Sequence[PolicyFinding]) -> int:
        if not findings:
            return 0
        for finding in findings:
            loc = finding.location
            where = ""
            if loc is not None:
                where = f"{loc.file}:{loc.line}: " if loc.line is not None else f"{loc.file}: "
            print(f"FAIL acronym: {where}{finding.message}", file=sys.stderr)
        return 1

    def _settings_from_config(self, config: dict[str, Any]) -> tuple[tuple[str, ...], Path | None]:
        scan_roots = tuple(str(item) for item in config.get("scan_roots", ["."]))
        allowlist_file = config.get("allowlist_file")
        allowlist_path = Path(str(allowlist_file)) if allowlist_file else None
        return scan_roots, allowlist_path

    def _require_allowlist_path(self, allowlist_path: Path | None) -> Path:
        if allowlist_path is None:
            msg = "acronym allowlist_file is required in gate config"
            raise ValueError(msg)
        if self._root is None:
            msg = "scan root is not bound"
            raise RuntimeError(msg)
        if not allowlist_path.is_absolute():
            return self._root / allowlist_path
        return allowlist_path

    def _load_allowlist(self, path: Path) -> set[str]:
        if not path.is_file():
            return set()
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            msg = f"acronym allowlist must be a YAML mapping: {path}"
            raise ValueError(msg)
        return {str(key) for key in raw}

    def _scan_paths(self) -> list[AcronymViolation]:
        if self._root is None:
            msg = "scan root is not bound"
            raise RuntimeError(msg)
        violations: list[AcronymViolation] = []
        scoped_files = scope_paths_from_env()
        if scoped_files:
            file_paths = [self._root / rel for rel in scoped_files]
        else:
            file_paths = self._iter_markdown_files()
        for file_path in file_paths:
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(self._root).as_posix()
            if self._ignores and self._ignores.is_ignored(rel):
                continue
            text = file_path.read_text(encoding="utf-8")
            violations.extend(self._find_violations_in_text(text, path=rel))
        return violations

    def _iter_markdown_files(self) -> list[Path]:
        if self._root is None:
            return []
        files: list[Path] = []
        for root in self._scan_roots:
            candidate = self._root / root
            if candidate.is_file():
                files.append(candidate)
                continue
            if candidate.is_dir():
                files.extend(sorted(candidate.rglob("*.md")))
                files.extend(sorted(candidate.rglob("*.mdc")))
        return files

    def _find_violations_in_text(self, text: str, *, path: str) -> list[AcronymViolation]:
        prose = self.strip_markdown_code(text)
        violations: list[AcronymViolation] = []
        for line_no, line in enumerate(prose.splitlines(), start=1):
            for token in self._find_violations_in_line(line):
                violations.append(AcronymViolation(path=path, line=line_no, token=token))
        return violations

    def _find_violations_in_line(self, line: str) -> list[str]:
        tokens: list[str] = []
        for match in ACRONYM_RE.finditer(line):
            token = match.group(0)
            if token in BUILTIN_EXEMPT or token in self._allowlisted:
                continue
            tokens.append(token)
        return tokens

    @staticmethod
    def _findings_from_violations(violations: list[AcronymViolation]) -> list[PolicyFinding]:
        return [
            PolicyFinding(
                rule_id="undocumented-acronym",
                message=f"undocumented acronym {item.token!r}",
                location=FindingLocation(file=item.path, line=item.line),
            )
            for item in violations
        ]


def main(argv: list[str] | None = None) -> int:
    return AcronymAllowlistGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
