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


def strip_markdown_code(text: str) -> str:
    without_fences = FENCED_CODE_BLOCK_RE.sub("", text)
    return INLINE_CODE_RE.sub("", without_fences)


def load_allowlist(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"acronym allowlist must be a YAML mapping: {path}"
        raise ValueError(msg)
    return {str(key) for key in raw}


def find_violations_in_line(line: str, *, allowlisted: set[str]) -> list[str]:
    tokens: list[str] = []
    for match in ACRONYM_RE.finditer(line):
        token = match.group(0)
        if token in BUILTIN_EXEMPT or token in allowlisted:
            continue
        tokens.append(token)
    return tokens


def find_violations_in_text(
    text: str,
    *,
    path: str,
    allowlisted: set[str],
) -> list[AcronymViolation]:
    prose = strip_markdown_code(text)
    violations: list[AcronymViolation] = []
    for line_no, line in enumerate(prose.splitlines(), start=1):
        for token in find_violations_in_line(line, allowlisted=allowlisted):
            violations.append(AcronymViolation(path=path, line=line_no, token=token))
    return violations


def iter_markdown_files(scan_roots: tuple[str, ...], repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root in scan_roots:
        candidate = repo_root / root
        if candidate.is_file():
            files.append(candidate)
            continue
        if candidate.is_dir():
            files.extend(sorted(candidate.rglob("*.md")))
            files.extend(sorted(candidate.rglob("*.mdc")))
    return files


def scan_paths(
    *,
    repo_root: Path,
    allowlist_path: Path,
    scan_roots: tuple[str, ...],
    ignores: EffectiveIgnores | None = None,
) -> list[AcronymViolation]:
    allowlisted = load_allowlist(allowlist_path)
    violations: list[AcronymViolation] = []
    scoped_files = scope_paths_from_env()
    if scoped_files:
        file_paths = [repo_root / rel for rel in scoped_files]
    else:
        file_paths = iter_markdown_files(scan_roots, repo_root)
    for file_path in file_paths:
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo_root).as_posix()
        if ignores and ignores.is_ignored(rel):
            continue
        text = file_path.read_text(encoding="utf-8")
        violations.extend(find_violations_in_text(text, path=rel, allowlisted=allowlisted))
    return violations


def findings_from_violations(
    violations: list[AcronymViolation],
) -> list[PolicyFinding]:
    return [
        PolicyFinding(
            rule_id="undocumented-acronym",
            message=f"undocumented acronym {item.token!r}",
            location=FindingLocation(file=item.path, line=item.line),
        )
        for item in violations
    ]


def settings_from_config(config: dict[str, Any]) -> tuple[tuple[str, ...], Path | None]:
    scan_roots = tuple(str(item) for item in config.get("scan_roots", ["."]))
    allowlist_file = config.get("allowlist_file")
    allowlist_path = Path(str(allowlist_file)) if allowlist_file else None
    return scan_roots, allowlist_path


def require_allowlist_path(root: Path, allowlist_path: Path | None) -> Path:
    if allowlist_path is None:
        msg = "acronym allowlist_file is required in gate config"
        raise ValueError(msg)
    if not allowlist_path.is_absolute():
        return root / allowlist_path
    return allowlist_path


class AcronymAllowlistGate(PolicyGate):
    gate_id: ClassVar[str] = "acronym-allowlist"
    description: ClassVar[str] = "Documented-acronym gate."

    def resolve_allowlist(self, root: Path, config: Mapping[str, Any]) -> set[str]:
        # Token allowlists are loaded inside collect_findings / scan_paths.
        return set()

    def collect_findings(
        self,
        *,
        root: Path,
        config: Mapping[str, Any],
        allowlist: set[str],
        ignores: EffectiveIgnores | None,
    ) -> Sequence[PolicyFinding]:
        scan_roots, allowlist_path = settings_from_config(dict(config))
        violations = scan_paths(
            repo_root=root,
            allowlist_path=require_allowlist_path(root, allowlist_path),
            scan_roots=scan_roots,
            ignores=ignores,
        )
        return findings_from_violations(violations)

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


def main(argv: list[str] | None = None) -> int:
    return AcronymAllowlistGate().main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
