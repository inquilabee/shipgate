from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from shipgate.frontend.web.app import create_app


def test_create_app_loads_project_catalog_overlay(tmp_path: Path):
    catalog_dir = tmp_path / ".shipgate" / "catalog" / "tools"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "overlay.demo.yaml").write_text(
        """
overlay.demo:
  executable: true
  modes: [check]
  normalizer: generic_exit
""",
        encoding="utf-8",
    )
    app = create_app(tmp_path, require_ui_token=False)
    assert "overlay.demo" in app.state.catalog.tools
