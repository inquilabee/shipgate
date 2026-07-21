from shipgate.domain.reports import SCHEMA_VERSION, report_json_schema


def test_report_json_schema_has_required_fields():
    schema = report_json_schema()
    assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION
    assert "check_report" in schema["$defs"]
