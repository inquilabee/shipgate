from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.gates.ignore import EffectiveIgnores
from shipgate.policy.core.finding import FindingLocation
from shipgate.policy.module_size import (
    ModuleSizeGate,
    check_file_size,
    count_non_blank_lines,
    should_skip_file,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_count_non_blank_lines_skips_whitespace_only() -> None:
    text = "a\n\n  \nb\n"
    assert count_non_blank_lines(text) == 2


def test_check_file_size_module_cap() -> None:
    finding = check_file_size("a.py", 501, module_max=500, portfolio_max=1000)
    assert finding is not None
    assert finding.rule_id == "module-size"
    assert finding.message == "a.py has 501 lines (module cap 500)"
    assert finding.location == FindingLocation(file="a.py", line=1)


def test_check_file_size_portfolio_cap_when_below_module() -> None:
    finding = check_file_size("a.py", 600, module_max=800, portfolio_max=500)
    assert finding is not None
    assert "portfolio cap 500" in finding.message


def test_should_skip_allowlisted_and_ignored() -> None:
    assert should_skip_file("skip/me.py", {"skip/me.py"}, None) is True
    ignores = EffectiveIgnores(path_patterns=("ignored/**",))
    assert should_skip_file("ignored/x.py", set(), ignores) is True
    assert should_skip_file("keep.py", set(), ignores) is False


def test_should_skip_allowlist_exact_match_no_leading_dot_slash() -> None:
    assert should_skip_file("./skip/me.py", {"skip/me.py"}, None) is False
    assert should_skip_file("skip/me.py", {"skip/me.py"}, None) is True


def test_should_skip_allowlist_no_backslash_normalization() -> None:
    assert should_skip_file(r"skip\me.py", {"skip/me.py"}, None) is False


def test_scan_respects_scope_paths(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "ok.py").write_text("x\n", encoding="utf-8")
    big = tmp_path / "big.py"
    big.write_text("\n".join(f"l{i}" for i in range(10)) + "\n", encoding="utf-8")
    monkeypatch.setenv("SHIPGATE_SCOPE_PATHS", "big.py")
    findings = ModuleSizeGate().collect_findings(
        root=tmp_path,
        config={"module_max_lines": 5, "portfolio_max_lines": 100, "scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert len(findings) == 1
    assert findings[0].location is not None
    assert findings[0].location.file == "big.py"


def test_run_gate_writes_findings_and_fails(tmp_path: Path) -> None:
    (tmp_path / "big.py").write_text("\n".join(["x"] * 10) + "\n", encoding="utf-8")
    config = {
        "scan_roots": ["."],
        "portfolio_max_lines": 100,
        "module_max_lines": 5,
    }
    report = tmp_path / "report.json"
    code = ModuleSizeGate().run(
        root=tmp_path,
        config=config,
        report_path=report,
    )
    assert code == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert len(payload["findings"]) == 1


def test_scan_scope_path_leading_dot_slash_not_allowlisted(tmp_path: Path, monkeypatch) -> None:
    big = tmp_path / "big.py"
    big.write_text("\n".join(f"l{i}" for i in range(10)) + "\n", encoding="utf-8")
    monkeypatch.setenv("SHIPGATE_SCOPE_PATHS", "./big.py")
    findings = ModuleSizeGate().collect_findings(
        root=tmp_path,
        config={"module_max_lines": 5, "portfolio_max_lines": 100, "scan_roots": ["."]},
        allowlist={"big.py"},
        ignores=None,
    )
    assert len(findings) == 1
    assert findings[0].location is not None
    assert findings[0].location.file == "./big.py"
