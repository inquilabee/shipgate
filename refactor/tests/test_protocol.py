from refactor.protocol import Hit, Location, RuleKind, Suggestion


def test_hit_round_trip_fields() -> None:
    suggestion = Suggestion(before="a", after="b", message="use get")
    hit = Hit(
        rule_id="default-get",
        message="Prefer dict.get",
        location=Location(path="x.py", line=3, column=0),
        suggestion=suggestion,
    )
    assert hit.rule_id == "default-get"
    assert hit.suggestion is not None
    assert hit.suggestion.after == "b"
    assert RuleKind.REFACTOR.value == "refactor"
