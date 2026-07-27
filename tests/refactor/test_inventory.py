from refactor.inventory import load_inventory


def test_inventory_has_default_get_native() -> None:
    entries = load_inventory()
    by_id = {e.id: e for e in entries}
    assert "default-get" in by_id
    assert by_id["default-get"].status == "native"
    assert len(entries) >= 150
