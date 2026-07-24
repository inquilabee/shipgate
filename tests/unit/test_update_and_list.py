from unittest.mock import MagicMock

from shipgate.app import InstallCommand, ShipGateApp
from shipgate.domain.catalog import Catalog, InstallDefinition, SuiteDefinition, ToolDefinition
from shipgate.domain.modes import RunMode


def test_update_force_reinstall(monkeypatch, tmp_path):
    tool = ToolDefinition(
        id="demo.tool",
        executable="demo",
        modes=(RunMode.CHECK,),
        install=InstallDefinition(manager="python", package="demo", version="1.2.3"),
    )
    catalog = Catalog(
        tools={"demo.tool": tool},
        suites={"standard": SuiteDefinition(id="standard", members=("demo.tool",))},
    )
    called: dict[str, object] = {}

    def fake_install_suite(project_root, suite_id, catalog, *, force=False):
        called["force"] = force
        called["suite"] = suite_id
        called["catalog"] = catalog
        return project_root / "manifest.json"

    monkeypatch.setattr("shipgate.app.install_suite", fake_install_suite)
    monkeypatch.setattr(
        "shipgate.app.ProjectConfigLoader.load",
        lambda **_kwargs: MagicMock(suite="standard"),
    )
    app = ShipGateApp(catalog=catalog)
    assert app.update(InstallCommand(project_root=tmp_path)) == 0
    assert called["force"] is True
    assert called["suite"] == "standard"
    assert called["catalog"] is catalog


def test_list_tools_filters_by_tag():
    catalog = Catalog(
        tools={
            "a.tool": ToolDefinition(
                id="a.tool",
                executable="a",
                modes=(RunMode.CHECK,),
                tags=("security",),
            ),
            "b.tool": ToolDefinition(id="b.tool", executable="b", modes=(RunMode.CHECK,)),
        },
        suites={},
    )
    app = ShipGateApp(catalog=catalog)
    assert app.list_tools(tag="security") == "a.tool\n"
    assert "b.tool" in app.list_tools()
