from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.project.suggest import suggest_tools
from shipgate.runtime.installers.version_spec import npm_package_spec, pip_package_spec


def test_suggest_hadolint_when_dockerfile_present(tmp_path: Path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.13\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    lines = suggest_tools(tmp_path, catalog)
    assert any("hadolint.check" in line for line in lines)


def test_suggest_skips_without_matching_files(tmp_path: Path):
    catalog = CatalogLoader.load()
    lines = suggest_tools(tmp_path, catalog)
    assert not any("hadolint.check" in line for line in lines)


def test_pip_package_spec_exact_pin():
    assert pip_package_spec("ruff", "0.15.22") == "ruff==0.15.22"
    assert pip_package_spec("ruff", "==0.15.22") == "ruff==0.15.22"
    assert pip_package_spec("ruff", ">=0.6") == "ruff>=0.6"


def test_npm_package_spec_exact_pin():
    assert npm_package_spec("jscpd", "5.0.12") == "jscpd@5.0.12"
