from pathlib import Path

from shipgate.frontend.domain.finding_context import source_contexts
from shipgate.frontend.domain.models import FindingCategory, FindingRecord


def test_source_context_reads_snippet(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    file_path = source / "app.py"
    lines = [f"line {index}" for index in range(1, 11)]
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    finding = FindingRecord(
        id="f1",
        run_id="run-1",
        check_id="ruff.lint",
        tool_id="ruff.lint",
        rule_id="F401",
        severity="error",
        message="unused import",
        file="src/app.py",
        line=5,
        category=FindingCategory.CODE,
    )
    contexts = source_contexts(tmp_path, [finding])
    assert "f1" in contexts
    snippet = contexts["f1"]
    numbers = [line.number for line in snippet.lines]
    assert 5 in numbers
    assert any(line.highlighted for line in snippet.lines)
