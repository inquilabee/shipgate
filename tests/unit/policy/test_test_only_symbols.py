from __future__ import annotations

from shipgate.policy.core.test_paths import is_test_path
from shipgate.policy.test_only_symbols import TestOnlySymbolsGate


def test_is_test_path_patterns() -> None:
    assert is_test_path("tests/unit/test_foo.py")
    assert is_test_path("test/test_foo.py")
    assert is_test_path("src/pkg/test_helpers.py")
    assert is_test_path("src/pkg/foo_test.py")
    assert is_test_path("src/pkg/mytest_util.py")
    assert is_test_path("tests/conftest.py")
    assert is_test_path("conftest.py")
    assert not is_test_path("src/shipgate/policy/module_size.py")
    assert not is_test_path("src/shipgate/texture.py")


def test_flags_method_only_used_in_tests(tmp_path, monkeypatch) -> None:
    prod = tmp_path / "app.py"
    prod.write_text(
        "class Service:\n"
        "    def only_for_tests(self):\n"
        "        return 1\n"
        "    def used_in_prod(self):\n"
        "        return 2\n"
        "\n"
        "def call_prod(service):\n"
        "    return service.used_in_prod()\n",
        encoding="utf-8",
    )
    test = tmp_path / "tests" / "test_app.py"
    test.parent.mkdir()
    test.write_text(
        "from app import Service\n\ndef test_only():\n    assert Service().only_for_tests() == 1\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = TestOnlySymbolsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    messages = [f.message for f in findings]
    assert any("only_for_tests" in msg for msg in messages)
    assert all("used_in_prod" not in msg for msg in messages)


def test_flags_class_only_used_in_tests(tmp_path, monkeypatch) -> None:
    (tmp_path / "models.py").write_text(
        "class TestOnlyModel:\n"
        "    pass\n"
        "\n"
        "class ProdModel:\n"
        "    pass\n"
        "\n"
        "def make_prod():\n"
        "    return ProdModel()\n",
        encoding="utf-8",
    )
    test = tmp_path / "tests" / "test_models.py"
    test.parent.mkdir()
    test.write_text(
        "from models import TestOnlyModel\n"
        "\n"
        "def test_model():\n"
        "    assert TestOnlyModel() is not None\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = TestOnlySymbolsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert any("TestOnlyModel" in f.message for f in findings)
    assert all("ProdModel" not in f.message for f in findings)


def test_allowlist_symbol_and_file(tmp_path, monkeypatch) -> None:
    (tmp_path / "app.py").write_text(
        "def helper_a():\n    return 1\n\ndef helper_b():\n    return 2\n",
        encoding="utf-8",
    )
    test = tmp_path / "test_app.py"
    test.write_text(
        "from app import helper_a, helper_b\n"
        "\n"
        "def test_helpers():\n"
        "    assert helper_a() == 1\n"
        "    assert helper_b() == 2\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = TestOnlySymbolsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist={"app.py:helper_a"},
        ignores=None,
    )
    assert all("helper_a" not in f.message for f in findings)
    assert any("helper_b" in f.message for f in findings)


def test_production_import_counts_as_use(tmp_path, monkeypatch) -> None:
    (tmp_path / "api.py").write_text(
        "def load_catalog():\n    return {}\n",
        encoding="utf-8",
    )
    (tmp_path / "__init__.py").write_text(
        "from api import load_catalog\n\n__all__ = ['load_catalog']\n",
        encoding="utf-8",
    )
    test = tmp_path / "tests" / "test_api.py"
    test.parent.mkdir()
    test.write_text(
        "from api import load_catalog\n\ndef test_load():\n    assert load_catalog() == {}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = TestOnlySymbolsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert all("load_catalog" not in f.message for f in findings)
