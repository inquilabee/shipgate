from shipgate.domain.reports import RunReport


def test_roundtrip():
    report = RunReport(run_id="x", suite="s", mode="check", status="passed")
    restored = RunReport.from_dict(report.to_dict())
    assert restored.run_id == "x"
    assert restored.suite == "s"
