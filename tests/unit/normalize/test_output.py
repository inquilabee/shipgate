from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.core import read_tool_output
from shipgate.runtime.executor import ProcessResult
from shipgate.runtime.session.check_runner import OutputFileSnapshot


def test_read_tool_output_prefers_file_when_stdout_is_progress_bar(tmp_path: Path):
    tool = CatalogLoader.load().get_tool("bandit.scan")
    output_path = tmp_path / "bandit.scan.json"
    output_path.write_text('{"results": []}', encoding="utf-8")
    resolved = ResolvedRequest(
        runnable="bandit.scan",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(output=output_path, format="json"),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=output_path,
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=0,
        stdout="Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00\n",
        stderr="",
        duration_ms=1,
        output_files=(output_path,),
    )
    assert read_tool_output(resolved, result) == '{"results": []}'


def test_read_tool_output_ignores_leftover_file_when_not_written_this_run(tmp_path: Path):
    tool = CatalogLoader.load().get_tool("bandit.scan")
    output_path = tmp_path / "bandit.scan.json"
    output_path.write_text('{"results": ["STALE"]}', encoding="utf-8")
    resolved = ResolvedRequest(
        runnable="bandit.scan",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(output=output_path, format="json"),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=output_path,
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=2,
        stdout="",
        stderr="tool crashed",
        duration_ms=1,
    )
    assert read_tool_output(resolved, result) == ""


def test_output_file_snapshot_treats_new_file_as_written(tmp_path: Path):
    path = tmp_path / "out.json"
    snapshot = OutputFileSnapshot.capture(path)
    path.write_text("{}", encoding="utf-8")
    assert snapshot.written_paths() == (path,)


def test_output_file_snapshot_ignores_unchanged_leftover(tmp_path: Path):
    path = tmp_path / "out.json"
    path.write_text("STALE", encoding="utf-8")
    snapshot = OutputFileSnapshot.capture(path)
    assert snapshot.written_paths() == ()
