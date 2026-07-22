from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import Finding
from shipgate.normalize.base import BaseNormalizer
from shipgate.normalize.json_base import JsonItemsNormalizer
from shipgate.runtime.executor import ProcessResult


class StubJsonNormalizer(JsonItemsNormalizer):
    items_key = "results"
    invalid_message = "invalid stub output"

    def item_to_finding(self, item: dict, check_id: str) -> Finding:
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("rule", "STUB")),
            severity="error",
            message=str(item.get("message", "")),
            location=None,
        )


def test_json_items_normalizer_is_base_normalizer():
    assert isinstance(StubJsonNormalizer(), BaseNormalizer)


def test_json_items_normalizer_maps_keyed_results(tmp_path):
    tool = ToolDefinition(id="stub.check", executable="stub", modes=(RunMode.CHECK,))
    request = ResolvedRequest(
        runnable="stub.check",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=1,
        stdout='{"results": [{"rule": "X", "message": "bad"}]}',
        stderr="",
        duration_ms=1,
    )
    report = StubJsonNormalizer().normalize(request, result)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "X"
