from shipgate.domain.reports import Finding
from shipgate.normalize.core import BaseNormalizer, JsonItemsNormalizer


class StubJsonNormalizer(JsonItemsNormalizer):
    items_key = "results"
    invalid_message = "invalid stub output"

    def item_to_finding(self, item: dict, check_id: str) -> Finding:  # ruff:ignore[no-self-use]
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("rule", "STUB")),
            severity="error",
            message=str(item.get("message", "")),
            location=None,
        )


def test_json_items_normalizer_is_base_normalizer():
    assert isinstance(StubJsonNormalizer(), BaseNormalizer)


def test_json_items_normalizer_maps_keyed_results(make_resolved_request, make_process_result):
    request = make_resolved_request(tool_id="stub.check", executable="stub")
    result = make_process_result(
        exit_code=1,
        stdout='{"results": [{"rule": "X", "message": "bad"}]}',
    )
    report = StubJsonNormalizer().normalize(request, result)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "X"


def test_empty_stdout_nonzero_exit_is_tool_exit(make_resolved_request, make_process_result):
    request = make_resolved_request(tool_id="stub.check", executable="stub")
    result = make_process_result(exit_code=1, stdout="", stderr="Failed to install packages")
    report = StubJsonNormalizer().normalize(request, result)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "TOOL_EXIT"
    assert "Failed to install packages" in report.findings[0].message
