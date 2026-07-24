from __future__ import annotations

from shipgate.policy.repeated_strings import RepeatedStringsGate


def test_collect_skips_docstrings() -> None:
    source = '''"""Module doc."""

def fn():
    """Fn doc."""
    return "x" + "x" + "x"
'''
    hits = RepeatedStringsGate.collect_string_literals(source)
    assert hits.count("x") == 3
    assert '"""Module doc."""' not in hits
    assert all(value != "Module doc." for value in hits)
    assert all(value != "Fn doc." for value in hits)


def test_flags_repeated_string(tmp_path, monkeypatch) -> None:
    (tmp_path / "app.py").write_text(
        "def build():\n"
        '    a = "repeated-token"\n'
        '    b = "repeated-token"\n'
        '    c = "repeated-token"\n'
        "    return a + b + c\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist=set(),
        ignores=None,
    )
    assert len(findings) == 1
    assert "repeated-token" in findings[0].message
    assert "constant" in findings[0].message.lower()


def test_respects_min_occurrences_and_length(tmp_path, monkeypatch) -> None:
    (tmp_path / "app.py").write_text(
        'a = "ab"\nb = "ab"\nc = "ab"\nd = "long-enough"\ne = "long-enough"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist=set(),
        ignores=None,
    )
    assert findings == []


def test_skips_python_identifiers(tmp_path, monkeypatch) -> None:
    (tmp_path / "app.py").write_text(
        'a = "store_true"\nb = "store_true"\nc = "store_true"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist=set(),
        ignores=None,
    )
    assert findings == []


def test_skips_test_paths_by_default(tmp_path, monkeypatch) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        'a = "repeated-token"\nb = "repeated-token"\nc = "repeated-token"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist=set(),
        ignores=None,
    )
    assert findings == []

    (tmp_path / "app.py").write_text(
        'a = "skip-me-please"\nb = "skip-me-please"\nc = "skip-me-please"\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    by_file = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist={"app.py"},
        ignores=None,
    )
    assert by_file == []
    by_string = RepeatedStringsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "min_occurrences": 3, "min_length": 4},
        allowlist={"string:skip-me-please"},
        ignores=None,
    )
    assert by_string == []
