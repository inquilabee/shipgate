from refactor.inventory import (
    inventory_by_id,
    load_inventory,
    rule_pack_selected,
)
from refactor.registry import RULES


def test_inventory_has_default_get_native() -> None:
    entries = load_inventory()
    by_id = {e.id: e for e in entries}
    assert "default-get" in by_id
    assert by_id["default-get"].status == "native"
    assert len(entries) >= 150


def test_assign_if_exp_inventory_is_native() -> None:
    entry = inventory_by_id()["assign-if-exp"]
    assert entry.status == "native"
    assert any(rule.rule_id == "assign-if-exp" for rule in RULES)


def test_rule_pack_selected_unknown_id_is_fail_closed() -> None:
    assert rule_pack_selected("not-a-real-rule", ()) is False
    assert rule_pack_selected("not-a-real-rule", frozenset({"gpsg"})) is False


def test_registered_rules_are_in_inventory() -> None:
    by_id = inventory_by_id()
    missing = sorted(rule.rule_id for rule in RULES if rule.rule_id not in by_id)
    assert not missing


def test_pack_inventory_rules_are_registered_or_stub() -> None:
    registered = {rule.rule_id for rule in RULES}
    pack_entries = tuple(entry for entry in load_inventory() if entry.packs)
    stubs = {entry.id for entry in pack_entries if entry.status == "stub"}
    shipped = {entry.id for entry in pack_entries if entry.status != "stub"}
    assert stubs.isdisjoint(registered)
    assert shipped <= registered
