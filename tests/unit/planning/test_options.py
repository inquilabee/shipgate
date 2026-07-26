from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.project import CheckBinding, ProjectConfig
from shipgate.planning.core.option_resolver import OptionResolver


def test_ty_check_default_format_from_catalog():
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ty.check")
    merged, sources = OptionResolver(ProjectConfig(), Path(), tool)._resolve_sources(
        NormalizedOptions()
    )
    assert merged.format == "gitlab"
    assert sources["format"] == "tool_default"


def test_option_resolver_merges_precedence(tmp_path: Path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ruff.lint")
    merged, sources = OptionResolver(ProjectConfig(), tmp_path, tool).resolve(
        NormalizedOptions(verbose=True),
        mode=RunMode.CHECK,
        check_id=tool.id,
        target=tmp_path,
    )
    assert merged.verbose is True
    assert sources["verbose"] == "cli"
    assert sources["check"] == "shipgate_default"
    assert merged.fix is not True


def test_option_resolver_defaults_fix_in_apply_mode(tmp_path: Path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ruff.lint")
    merged, sources = OptionResolver(ProjectConfig(), tmp_path, tool).resolve(
        NormalizedOptions(),
        mode=RunMode.APPLY,
        check_id=tool.id,
        target=tmp_path,
    )
    assert merged.fix is True
    assert sources["fix"] == "shipgate_default"


def test_option_resolver_injects_radon_metric_bindings(tmp_path: Path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("radon.mi")
    binding = CheckBinding(
        runnable="radon.mi",
        threshold="B",
        median_mode="threshold",
        median_threshold=55.0,
        p95_mode="threshold",
        p95_threshold=80.0,
    )
    merged, sources = OptionResolver(
        ProjectConfig(check_bindings=(binding,)),
        tmp_path,
        tool,
    ).resolve(
        NormalizedOptions(),
        mode=RunMode.CHECK,
        check_id=tool.id,
        target=tmp_path,
    )
    assert merged.threshold == "B"
    assert merged.extra["median_mode"] == "threshold"
    assert merged.extra["median_threshold"] == pytest.approx(55.0)
    assert merged.extra["p95_mode"] == "threshold"
    assert merged.extra["p95_threshold"] == pytest.approx(80.0)
    assert sources["median_mode"] == "project"
    assert sources["p95_mode"] == "project"
