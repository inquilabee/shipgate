"""Config schema constants."""

ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "suite",
        "env",
        "target",
        "error-format",
        "configs",
        "checks",
        "scopes",
        "error-formatters",
        "auto-install",
        "parallel",
        "fail-fast",
    }
)

ALLOWED_ENV_VALUES = frozenset({"managed", "system"})
ALLOWED_ERROR_FORMATS = frozenset({"json", "compact", "text", "github"})
ALLOWED_CONFIG_MODES = frozenset({"auto", "repo", "bundled"})
