from shipgate.catalog.loader import load_catalog
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.project import ProjectConfig
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
