from __future__ import annotations

from shipgate.policy.core.finding import FindingLocation
from shipgate.policy.module_private_vars import (
    ModulePrivateVarsGate,
    findings_for_file,
)


def test_finds_assignment_function_class() -> None:
    text = "_secret = 1\ndef _helper():\n    pass\nclass _Hidden:\n    pass\n"
    findings = findings_for_file("m.py", text)
    ids = {f.rule_id for f in findings}
    assert ids == {"private-assignment", "private-function", "private-class"}


def test_ignores_dunder_and_indented() -> None:
    text = "__all__ = []\nDef = 1\n    _indented = 1\n"
    assert findings_for_file("m.py", text) == []


def test_async_def_detected() -> None:
    findings = findings_for_file("m.py", "async def _go():\n    pass\n")
    assert findings[0].rule_id == "private-function"


def test_message_format_matches_grep_style() -> None:
    findings = findings_for_file("m.py", "_secret = 1\n")
    assert findings[0].message == "m.py:1:_secret = 1"
    assert findings[0].location == FindingLocation(file="m.py", line=1)


def test_scan_respects_allowlist(tmp_path, monkeypatch) -> None:
    (tmp_path / "bad.py").write_text("_x = 1\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("_y = 2\n", encoding="utf-8")
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ModulePrivateVarsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist={"ok.py"},
        ignores=None,
    )
    assert len(findings) == 1
    assert findings[0].location is not None
    assert findings[0].location.file == "bad.py"
