from __future__ import annotations

from shipgate.policy.acronym_allowlist import AcronymAllowlistGate


def collect_acronym_findings(tmp_path, monkeypatch, *, prose: str, allowlist_body: str):
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "guide.md").write_text(prose, encoding="utf-8")
    allowlist = tmp_path / "acronyms.yaml"
    allowlist.write_text(allowlist_body, encoding="utf-8")
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    return AcronymAllowlistGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["docs"], "allowlist_file": str(allowlist)},
        allowlist=set(),
        ignores=None,
    )


def test_flags_undocumented_acronym(tmp_path, monkeypatch) -> None:
    findings = collect_acronym_findings(
        tmp_path,
        monkeypatch,
        prose="The ZZQ pipeline runs nightly.\n",
        allowlist_body="UI: user interface\n",
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "undocumented-acronym"
    assert "ZZQ" in findings[0].message


def test_allowlisted_token_passes(tmp_path, monkeypatch) -> None:
    findings = collect_acronym_findings(
        tmp_path,
        monkeypatch,
        prose="The ZZQ pipeline runs nightly.\n",
        allowlist_body="ZZQ: custom pipeline name\n",
    )
    assert findings == []


def test_ignores_fenced_and_inline_code(tmp_path, monkeypatch) -> None:
    findings = collect_acronym_findings(
        tmp_path,
        monkeypatch,
        prose="Use `ZZQ` in config.\n\n```\nZZQ = 1\n```\n\nPlain ZZQ fails.\n",
        allowlist_body="{}\n",
    )
    assert len(findings) == 1
    assert findings[0].location is not None
    assert findings[0].location.file == "docs/guide.md"
    assert "ZZQ" in findings[0].message
