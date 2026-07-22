from shipgate.adapter.serialize import serialize_option
from shipgate.domain.catalog import CliOptionDefinition


def test_scalar():
    opt = CliOptionDefinition(flag="--config", style="scalar")
    assert serialize_option(opt, "cfg.toml") == ["--config", "cfg.toml"]


def test_scalar_tuple_uses_first_path():
    opt = CliOptionDefinition(flag="--config", style="scalar")
    assert serialize_option(opt, ("/path/cfg.toml",)) == ["--config", "/path/cfg.toml"]


def test_scalar_aggregate_repeat_emits_all_paths():
    opt = CliOptionDefinition(flag="--source", style="scalar", aggregate="repeat")
    assert serialize_option(opt, ("docs", "src")) == [
        "--source",
        "docs",
        "--source",
        "src",
    ]


def test_repeated():
    opt = CliOptionDefinition(flag="--exclude", style="repeated")
    assert serialize_option(opt, ("a", "b")) == ["--exclude", "a", "--exclude", "b"]


def test_joined():
    opt = CliOptionDefinition(flag="--rules", style="joined", separator=",")
    assert serialize_option(opt, ("E", "F")) == ["--rules", "E,F"]


def test_boolean_true():
    opt = CliOptionDefinition(flag="--check", style="boolean")
    assert serialize_option(opt, True) == ["--check"]


def test_boolean_false():
    opt = CliOptionDefinition(flag="--check", style="boolean")
    assert serialize_option(opt, False) == []


def test_positional():
    opt = CliOptionDefinition(style="positional")
    assert serialize_option(opt, ("src", "tests")) == ["src", "tests"]
