from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.project import ProjectConfig
from shipgate.planning.option_resolver import OptionResolver
from shipgate.planning.options import resolve_option_sources


def test_ty_check_default_format_from_catalog():
    catalog = load_catalog()
    tool = catalog.get_tool("ty.check")
    merged, sources = resolve_option_sources(
        cli_options=NormalizedOptions(),
        project=ProjectConfig(),
        tool=tool,
    )
    assert merged.format == "gitlab"
    assert sources["format"] == "tool_default"


def test_option_resolver_merges_precedence(tmp_path: Path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    merged, sources = OptionResolver().resolve(
        cli_options=NormalizedOptions(verbose=True),
        project=ProjectConfig(),
        tool=tool,
        mode=RunMode.CHECK,
        check_id=tool.id,
        project_root=tmp_path,
        target=tmp_path,
    )
    assert merged.verbose is True
    assert sources["verbose"] == "cli"
    assert sources["check"] == "shipgate_default"
    assert merged.fix is not True


def test_option_resolver_defaults_fix_in_apply_mode(tmp_path: Path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    merged, sources = OptionResolver().resolve(
        cli_options=NormalizedOptions(),
        project=ProjectConfig(),
        tool=tool,
        mode=RunMode.APPLY,
        check_id=tool.id,
        project_root=tmp_path,
        target=tmp_path,
    )
    assert merged.fix is True
    assert sources["fix"] == "shipgate_default"
