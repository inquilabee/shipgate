"""Gate scope path helpers."""

from pathlib import Path

from shipgate.domain.catalog import ScopeCriteria, ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.gates.scope_paths import gate_scope_entry, gate_scope_paths, gate_scope_rel_path


def make_resolved(tmp_path: Path, paths: tuple[Path, ...], *, delivery: str) -> ResolvedRequest:
    tool = ToolDefinition(
        id="gate.sample",
        executable="bash",
        scope=ScopeCriteria(delivery=delivery),
    )
    return ResolvedRequest(
        runnable="gate.sample",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=paths),
        option_sources={},
        extra_args=(),
        project_root=tmp_path.resolve(),
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def test_gate_scope_rel_path_rejects_outside_project(tmp_path: Path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    resolved = make_resolved(tmp_path, (), delivery="root")
    assert gate_scope_rel_path(resolved, outside) is None


def test_gate_scope_entry_root_delivery_includes_dirs(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    assert gate_scope_entry("root", src, "src") == "src"
    assert gate_scope_entry("root", tmp_path, ".") == "."


def test_gate_scope_paths_root_delivery(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    resolved = make_resolved(tmp_path, (Path("src"),), delivery="root")
    assert gate_scope_paths(resolved) == ("src",)
