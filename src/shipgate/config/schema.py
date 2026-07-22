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
        "workflow",
        "error-formatters",
        "auto-install",
        "parallel",
        "fail-fast",
        "changed-only",
        "since",
    }
)

ALLOWED_ENV_VALUES = frozenset({"managed", "system"})
ALLOWED_ERROR_FORMATS = frozenset({"json", "compact", "text", "github"})
ALLOWED_CONFIG_MODES = frozenset({"auto", "repo", "bundled"})
