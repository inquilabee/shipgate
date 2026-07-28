"""GPSG optional pack: enable gating and representative detects."""

from __future__ import annotations

from refactor.cli import main
from refactor.detector import check_rules
from refactor.inventory import load_inventory
from refactor.registry import RULES
from refactor.rules.bridge.ruff.gpsg.no_relative_imports import NoRelativeImportsBridge
from refactor.rules.bridge.ruff.gpsg.no_wildcard_imports import NoWildcardImportsBridge
from refactor.rules.bridge.ruff.gpsg.standard_import_aliases import (
    GPSG_IMPORT_ALIAS_BRIDGES,
)
from refactor.rules.native.gpsg.lambda_style import FilterLambdaToGeneratorRule
from refactor.rules.native.gpsg.naming import UpperCamelCaseClassesRule
from refactor.runner import check_paths

GPSG_IDS = frozenset(entry.id for entry in load_inventory() if "gpsg" in entry.packs)
# Sourcery 32 minus Py2-only do-not-use-has-key; avoid-global-variables remains inventory stub.
EXPECTED_GPSG_INVENTORY = 31


def test_inventory_has_gpsg_pack_without_py2_rules() -> None:
    assert len(GPSG_IDS) == EXPECTED_GPSG_INVENTORY
    assert "do-not-use-has-key" not in GPSG_IDS
    assert "avoid-global-variables" in GPSG_IDS
    stub = next(e for e in load_inventory() if e.id == "avoid-global-variables")
    assert stub.status == "stub"


def test_avoid_global_variables_not_registered() -> None:
    assert all(rule.rule_id != "avoid-global-variables" for rule in RULES)
    assert all(rule.rule_id != "do-not-use-has-key" for rule in RULES)


def test_gpsg_rules_excluded_without_enable() -> None:
    selected = {rule.rule_id for rule in check_rules()}
    assert selected.isdisjoint(GPSG_IDS - {"avoid-global-variables"})


def test_enable_gpsg_selects_shipped_rules() -> None:
    selected = {rule.rule_id for rule in check_rules(enable=frozenset({"gpsg"}))}
    shipped = GPSG_IDS - {"avoid-global-variables"}
    assert shipped <= selected
    assert "avoid-global-variables" not in selected


def test_enable_gpsg_import_subset() -> None:
    selected = {rule.rule_id for rule in check_rules(enable=frozenset({"gpsg-import"}))}
    assert "no-wildcard-imports" in selected
    assert "no-relative-imports" in selected
    assert "docstrings-for-classes" not in selected


def test_without_enable_strict_ignores_gpsg_fixtures(tmp_path, capsys) -> None:
    src = tmp_path / "sample.py"
    src.write_text("from os import *\nfrom . import x\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert all(hit.rule_id not in GPSG_IDS for hit in hits)
    main(["check", "--strict", str(tmp_path)])
    out = capsys.readouterr().out
    assert "no-wildcard-imports" not in out
    assert "no-relative-imports" not in out


def test_cli_enable_gpsg_reports_wildcard(tmp_path, capsys) -> None:
    src = tmp_path / "sample.py"
    src.write_text("from os import *\n", encoding="utf-8")
    assert main(["check", "--strict", "--enable", "gpsg", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "no-wildcard-imports" in out


def test_cli_list_shows_pack_metadata(capsys) -> None:
    assert main(["list", "--enable", "gpsg"]) == 0
    out = capsys.readouterr().out
    assert "no-wildcard-imports" in out
    assert "packs=gpsg" in out
    assert "enabled=True" in out


def test_no_wildcard_bridge_detects() -> None:
    hits = NoWildcardImportsBridge().detect("from os import *\n", "sample.py")
    assert hits
    assert hits[0].rule_id == "no-wildcard-imports"


def test_no_relative_bridge_needs_config() -> None:
    hits = NoRelativeImportsBridge().detect("from . import x\n", "pkg/sample.py")
    assert hits
    assert hits[0].rule_id == "no-relative-imports"


def test_shared_alias_bridge_maps_datetime() -> None:
    bridge = next(
        b
        for b in GPSG_IMPORT_ALIAS_BRIDGES
        if b.rule_id == "use-standard-name-for-aliases-datetime"
    )
    hits = bridge.detect("import datetime as dtime\n", "sample.py")
    assert hits
    assert hits[0].rule_id == "use-standard-name-for-aliases-datetime"
    assert not bridge.detect("import datetime as dt\n", "sample.py")


def test_filter_lambda_native() -> None:
    hits = FilterLambdaToGeneratorRule().detect(
        "filtered = filter(lambda x: x > 0, things)\n",
        "sample.py",
    )
    assert hits
    assert hits[0].rule_id == "filter-lambda-to-generator"


def test_upper_camel_native() -> None:
    hits = UpperCamelCaseClassesRule().detect("class snake_case:\n    pass\n", "s.py")
    assert hits
    assert not UpperCamelCaseClassesRule().detect("class SnakeCase:\n    pass\n", "s.py")


def test_enable_from_shipgate_yaml(tmp_path, monkeypatch, capsys) -> None:
    src = tmp_path / "sample.py"
    src.write_text("from os import *\n", encoding="utf-8")
    cfg = tmp_path / ".shipgate"
    cfg.mkdir()
    (cfg / "refactor.yaml").write_text("enable:\n  - gpsg\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["check", "--strict", str(src)]) == 1
    assert "no-wildcard-imports" in capsys.readouterr().out


def test_cli_explain_gpsg_rule(capsys) -> None:
    assert main(["explain", "no-wildcard-imports"]) == 0
    out = capsys.readouterr().out
    assert "no-wildcard-imports" in out
    assert "packs:" in out
