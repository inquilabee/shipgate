"""ApplyMode policy: auto / hint / off."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from refactor.cli import main, parse_args
from refactor.inventory import load_inventory
from refactor.protocol import ApplyMode, Hit, Location, RefactorRule, RuleKind
from refactor.registry import RULES
from refactor.runner import apply_auto_rule, fix_paths

# Former applier.py whitelist — guidance-only unless promoted with round-trip tests.
WHITELIST_HINT_RULE_IDS = frozenset(
    {
        "collection-to-bool",
        "remove-unnecessary-cast",
        "assign-if-exp",
        "identity-comprehension",
        "use-assigned-variable",
        "chain-compares",
        "convert-any-to-in",
        "inline-immediately-returned-variable",
        "merge-comparisons",
        "remove-redundant-continue",
    }
)


class AutoStubRule:
    rule_id = "auto-stub"
    kind = RuleKind.REFACTOR
    summary = "auto stub"
    apply_mode = ApplyMode.AUTO

    def detect(self, source: str, path: str) -> list[Hit]:
        return (
            []
            if "AUTO_MARK" not in source
            else [
                Hit(
                    rule_id=self.rule_id,
                    message="auto",
                    location=Location(path=path, line=1, column=1),
                )
            ]
        )

    def apply(self, source: str, hits: list[Hit]) -> str | None:
        _ = self, hits
        return source.replace("AUTO_MARK", "done")


class HintStubRule:
    rule_id = "hint-stub"
    kind = RuleKind.REFACTOR
    summary = "hint stub"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        return (
            []
            if "HINT_MARK" not in source
            else [
                Hit(
                    rule_id=self.rule_id,
                    message="hint",
                    location=Location(path=path, line=1, column=1),
                )
            ]
        )

    def apply(self, source: str, hits: list[Hit]) -> str | None:
        _ = self, hits
        return source.replace("HINT_MARK", "should-not-apply")


def test_registered_auto_rules_match_former_safe_apply() -> None:
    auto_ids = {rule.rule_id for rule in RULES if rule.apply_mode is ApplyMode.AUTO}
    assert auto_ids == {
        "aug-assign",
        "bin-op-identity",
        "boolean-if-exp-identity",
        "collection-into-set",
        "default-get",
        "dict-literal",
        "min-max-identity",
        "none-compare",
        "remove-redundant-pass",
        "simplify-boolean-comparison",
        "tuple-literal",
        "use-len",
        "yield-from",
    }


def test_reintroduce_else_is_off() -> None:
    rule = next(rule for rule in RULES if rule.rule_id == "reintroduce-else")
    assert rule.apply_mode is ApplyMode.OFF


def test_former_applier_whitelist_stays_hint() -> None:
    by_id = {rule.rule_id: rule for rule in RULES}
    assert all(by_id[rule_id].apply_mode is ApplyMode.HINT for rule_id in WHITELIST_HINT_RULE_IDS)


def test_fix_paths_applies_only_auto_not_hint(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text("AUTO_MARK\nHINT_MARK\n", encoding="utf-8")
    rules = cast("tuple[RefactorRule, ...]", (AutoStubRule(), HintStubRule()))
    changed = fix_paths([tmp_path], rules=rules)
    assert src in changed
    assert src.read_text(encoding="utf-8") == "done\nHINT_MARK\n"


def test_apply_auto_rule_skips_hint() -> None:
    source = "HINT_MARK\n"
    rule = cast("RefactorRule", HintStubRule())
    assert apply_auto_rule(rule, source, Path("sample.py")) == source


def test_default_check_reports_auto_only(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        "from typing import cast\n\ndef f(raw):\n    return cast(int, raw)\n",
        encoding="utf-8",
    )
    assert main(["check", str(tmp_path)]) == 0
    assert main(["check", "--strict", str(tmp_path)]) == 1


def test_inventory_loads_apply_mode_and_aliases_safe_apply(tmp_path: Path) -> None:
    inv = tmp_path / "rule_ids.yaml"
    inv.write_text(
        "- id: demo-auto\n"
        "  kind: refactor\n"
        "  status: native\n"
        "  safe_apply: true\n"
        "- id: demo-hint\n"
        "  kind: refactor\n"
        "  status: native\n"
        "  apply_mode: hint\n"
        "- id: demo-off\n"
        "  kind: refactor\n"
        "  status: native\n"
        '  apply_mode: "off"\n',
        encoding="utf-8",
    )
    entries = {entry.id: entry for entry in load_inventory(inv)}
    assert entries["demo-auto"].apply_mode is ApplyMode.AUTO
    assert entries["demo-hint"].apply_mode is ApplyMode.HINT
    assert entries["demo-off"].apply_mode is ApplyMode.OFF


def test_cli_explain_prints_examples(capsys) -> None:
    code = main(["explain", "remove-unnecessary-cast"])
    out = capsys.readouterr().out
    assert code == 0
    assert "remove-unnecessary-cast" in out
    assert "example_bad" in out or "before" in out.lower() or "cast(" in out


def test_fix_has_no_strict_flag() -> None:
    with pytest.raises(SystemExit):
        parse_args(["fix", "--strict", "."])


def test_strict_json_fills_catalog_examples_when_suggestion_absent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        "from typing import cast\n\ndef f(raw):\n    return cast(int, raw)\n",
        encoding="utf-8",
    )
    assert main(["check", "--strict", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "remove-unnecessary-cast" in out
    assert "cast(int, raw)" in out or "example" in out.lower()
