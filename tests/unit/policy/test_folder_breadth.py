from __future__ import annotations

from shipgate.policy.folder_breadth import FolderBreadthGate


def write_py_files(directory, count: int) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (directory / f"mod_{index}.py").write_text(f"x = {index}\n", encoding="utf-8")


def collect_breadth_findings(
    tmp_path,
    monkeypatch,
    *,
    file_count: int,
    max_allowed: int = 3,
    allowlist: set[str] | None = None,
):
    write_py_files(tmp_path / "pkg", file_count)
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    return FolderBreadthGate().collect_findings(
        root=tmp_path,
        config={
            "scan_roots": ["."],
            "max_allowed": max_allowed,
            "extensions": [".py"],
            "strict": True,
        },
        allowlist=allowlist or set(),
        ignores=None,
    )


def test_flags_over_broad_leaf_dir(tmp_path, monkeypatch) -> None:
    findings = collect_breadth_findings(tmp_path, monkeypatch, file_count=4)
    assert len(findings) == 1
    assert findings[0].rule_id == "folder-breadth"
    assert "pkg" in findings[0].message
    assert "4" in findings[0].message


def test_allowlisted_path_skipped(tmp_path, monkeypatch) -> None:
    findings = collect_breadth_findings(tmp_path, monkeypatch, file_count=4, allowlist={"pkg"})
    assert findings == []


def test_respects_max_allowed_threshold(tmp_path, monkeypatch) -> None:
    findings = collect_breadth_findings(tmp_path, monkeypatch, file_count=3)
    assert findings == []


def test_does_not_walk_review_venv_site_packages(tmp_path, monkeypatch) -> None:
    write_py_files(tmp_path / "pkg", 2)
    write_py_files(tmp_path / ".review-venv" / "lib" / "python3.13" / "site-packages" / "rich", 20)
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    gate = FolderBreadthGate()
    findings = gate.collect_findings(
        root=tmp_path,
        config={
            "scan_roots": ["."],
            "max_allowed": 3,
            "extensions": [".py"],
            "strict": True,
        },
        allowlist=set(),
        ignores=None,
    )
    assert findings == []
    extra = gate.report_extra(findings)
    assert extra is not None
    assert extra["leaf_dirs_scanned"] == 1


def test_does_not_walk_node_modules(tmp_path, monkeypatch) -> None:
    write_py_files(tmp_path / "pkg", 2)
    write_py_files(tmp_path / "node_modules" / "pkg", 20)
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    gate = FolderBreadthGate()
    findings = gate.collect_findings(
        root=tmp_path,
        config={
            "scan_roots": ["."],
            "max_allowed": 3,
            "extensions": [".py"],
            "strict": True,
        },
        allowlist=set(),
        ignores=None,
    )
    assert findings == []
    extra = gate.report_extra(findings)
    assert extra is not None
    assert extra["leaf_dirs_scanned"] == 1
