from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from refactor.cli import main
from refactor.protocol import Hit, Location, RuleKind
from refactor.registry import RULES
from refactor.rules.native.redundancy.lift_return_into_if import LiftReturnIntoIfRule
from refactor.rules.native.redundancy.reintroduce_else import ReintroduceElseRule
from refactor.rules.native.strings.remove_redundant_continue import (
    RemoveRedundantContinueRule,
)
from refactor.runner import (
    apply_safe_rule,
    check_paths,
    check_rules,
    fix_paths,
    iter_python_files,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

BEFORE = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d[key] if key in d else 0
    return value
"""

AFTER = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d.get(key, 0)
    return value
"""


def test_check_paths_finds_default_get(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(h.rule_id == "default-get" for h in hits)


def test_check_paths_populates_hit_location(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    hit = next(h for h in check_paths([tmp_path]) if h.rule_id == "default-get")
    assert hit.location.line == 2
    assert hit.location.column is not None


def test_default_check_rules_skip_inactive_bridges() -> None:
    assert any(getattr(rule, "delegates_to", None) is not None for rule in RULES)
    assert all(getattr(rule, "delegates_to", None) is None for rule in check_rules())
    assert check_rules(RULES) == RULES


def test_body_sequence_rules_populate_hit_locations() -> None:
    reintroduce_hit = ReintroduceElseRule().detect(
        "def f(failed):\n    if failed:\n        return None\n    recover()\n",
        "sample.py",
    )[0]
    lift_hit = LiftReturnIntoIfRule().detect(
        "def f(failed):\n    if failed:\n        return None\n    return recover()\n",
        "sample.py",
    )[0]
    assert reintroduce_hit.location.line == 2
    assert reintroduce_hit.location.column == 4
    assert lift_hit.location.line == 2
    assert lift_hit.location.column == 4


def test_body_cleanup_rules_populate_hit_locations() -> None:
    hit = RemoveRedundantContinueRule().detect(
        "for item in items:\n    process(item)\n    continue\n",
        "sample.py",
    )[0]
    assert hit.location.line == 3
    assert hit.location.column == 4


def test_iter_python_files_skips_gitignored_and_tool_dirs(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored.py\nignored_dir/\n", encoding="utf-8")
    visible = tmp_path / "visible.py"
    ignored_file = tmp_path / "ignored.py"
    ignored_dir = tmp_path / "ignored_dir"
    venv_dir = tmp_path / ".venv"
    shipgate_tools_dir = tmp_path / ".shipgate" / "tools"
    ignored_dir.mkdir()
    venv_dir.mkdir()
    shipgate_tools_dir.mkdir(parents=True)
    visible.write_text("x = 1\n", encoding="utf-8")
    ignored_file.write_text("x = 1\n", encoding="utf-8")
    (ignored_dir / "nested.py").write_text("x = 1\n", encoding="utf-8")
    (venv_dir / "site.py").write_text("x = 1\n", encoding="utf-8")
    (shipgate_tools_dir / "tool.py").write_text("x = 1\n", encoding="utf-8")

    assert iter_python_files([tmp_path]) == [visible]


def test_fix_paths_rewrites_safe_rules(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == AFTER
    hits = check_paths([tmp_path])
    assert not any(hit.rule_id == "default-get" for hit in hits)


MULTI_BEFORE = """\
def f(items=[]):
    cache = dict()
"""

MULTI_AFTER = """\
def f(items=[]):
    cache = {}
"""

NON_SAFE_RULE_IDS = frozenset(rule.rule_id for rule in RULES if not rule.safe_apply)


def test_fix_paths_applies_only_safe_rules(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(MULTI_BEFORE, encoding="utf-8")
    changed = fix_paths([tmp_path])
    assert src in changed
    assert src.read_text(encoding="utf-8") == MULTI_AFTER
    hits = check_paths([tmp_path])
    assert not any(hit.rule_id == "dict-literal" for hit in hits)
    assert any(hit.rule_id == "default-mutable-arg" for hit in hits)
    assert hits
    assert all(hit.rule_id in NON_SAFE_RULE_IDS for hit in hits)


def test_cli_list_includes_default_get(capsys) -> None:
    code = main(["list"])
    out = capsys.readouterr().out
    assert code == 0
    assert "default-get" in out
    assert "list-literal" in out
    assert "bridge=inactive delegates_to=" in out


def test_cli_check_exit_code(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(BEFORE, encoding="utf-8")
    assert main(["check", str(tmp_path)]) == 1


def test_cli_check_strict_reports_suggestion_only_rules(tmp_path: Path, capsys) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        "from typing import cast\n\ndef f(raw):\n    return cast(int, raw)\n",
        encoding="utf-8",
    )
    assert main(["check", str(tmp_path)]) == 0
    assert main(["check", "--strict", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "remove-unnecessary-cast" in out


def test_custom_detect_path_filter_not_bypassed_by_combined_visitor(
    tmp_path: Path,
) -> None:
    src = tmp_path / "module.py"
    src.write_text("def f():\n    if True:\n        return 1\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert not any(hit.rule_id == "no-conditionals-in-tests" for hit in hits)

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    test_src = tests_dir / "test_module.py"
    test_src.write_text("def test_f():\n    if True:\n        assert 1\n", encoding="utf-8")
    hits = check_paths([tmp_path])
    assert any(hit.rule_id == "no-conditionals-in-tests" for hit in hits)


class StillDetectingRule:
    rule_id = "still-detecting-stub"
    kind = RuleKind.REFACTOR
    summary = "Stub rule whose apply still leaves detectable hits"
    safe_apply = True

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        if "HIT_MARKER" not in source:
            return []
        return [
            Hit(
                rule_id=self.rule_id,
                message="marker present",
                location=Location(path=path, line=1, column=1),
            )
        ]

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, hits
        return source.replace("HIT_MARKER", "STILL_HAS_HIT_MARKER")


def test_apply_safe_rule_rejects_rewrite_that_still_detects() -> None:
    rule = StillDetectingRule()
    source = "x = HIT_MARKER\n"
    assert apply_safe_rule(rule, source, Path("sample.py")) == source
