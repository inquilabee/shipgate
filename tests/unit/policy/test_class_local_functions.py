from __future__ import annotations

from shipgate.policy.class_local_functions import ClassLocalFunctionsGate
from shipgate.policy.core.files import path_is_allowlisted


def test_path_is_allowlisted_supports_directory_prefix() -> None:
    assert path_is_allowlisted("src/pkg/utils/helpers.py", {"src/pkg/utils"})
    assert path_is_allowlisted("src/pkg/utils", {"src/pkg/utils"})
    assert not path_is_allowlisted("src/pkg/other/helpers.py", {"src/pkg/utils"})


def test_flags_module_function_only_used_in_one_class(tmp_path, monkeypatch) -> None:
    (tmp_path / "service.py").write_text(
        "def _format_name(value):\n"
        "    return value.strip()\n"
        "\n"
        "class Service:\n"
        "    def render(self, value):\n"
        "        return _format_name(value)\n"
        "\n"
        "    def render_upper(self, value):\n"
        "        return _format_name(value).upper()\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert len(findings) == 1
    assert "_format_name" in findings[0].message
    assert "staticmethod" in findings[0].message


def test_suggests_classmethod_when_first_arg_is_cls(tmp_path, monkeypatch) -> None:
    (tmp_path / "factory.py").write_text(
        "def _build(cls, value):\n"
        "    return cls(value)\n"
        "\n"
        "class Factory:\n"
        "    def make(self, value):\n"
        "        return _build(Factory, value)\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert len(findings) == 1
    assert "classmethod" in findings[0].message


def test_flags_public_module_function_only_used_in_one_class(tmp_path, monkeypatch) -> None:
    (tmp_path / "service.py").write_text(
        "def format_name(value):\n"
        "    return value.strip()\n"
        "\n"
        "class Service:\n"
        "    def render(self, value):\n"
        "        return format_name(value)\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert len(findings) == 1
    assert "format_name" in findings[0].message
    assert "staticmethod" in findings[0].message


def test_private_only_skips_public_functions(tmp_path, monkeypatch) -> None:
    (tmp_path / "service.py").write_text(
        "def format_name(value):\n"
        "    return value.strip()\n"
        "\n"
        "class Service:\n"
        "    def render(self, value):\n"
        "        return format_name(value)\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."], "private_only": True},
        allowlist=set(),
        ignores=None,
    )
    assert findings == []


def test_skips_when_used_outside_class(tmp_path, monkeypatch) -> None:
    (tmp_path / "service.py").write_text(
        "def _format_name(value):\n"
        "    return value.strip()\n"
        "\n"
        "class Service:\n"
        "    def render(self, value):\n"
        "        return _format_name(value)\n"
        "\n"
        "def public_api(value):\n"
        "    return _format_name(value)\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist=set(),
        ignores=None,
    )
    assert findings == []


def test_allowlist_utils_directory(tmp_path, monkeypatch) -> None:
    utils = tmp_path / "pkg" / "utils"
    utils.mkdir(parents=True)
    (utils / "helpers.py").write_text(
        "def _only_for_parser(value):\n"
        "    return value\n"
        "\n"
        "class Parser:\n"
        "    def parse(self, value):\n"
        "        return _only_for_parser(value)\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SHIPGATE_SCOPE_PATHS", raising=False)
    findings = ClassLocalFunctionsGate().collect_findings(
        root=tmp_path,
        config={"scan_roots": ["."]},
        allowlist={"pkg/utils"},
        ignores=None,
    )
    assert findings == []
