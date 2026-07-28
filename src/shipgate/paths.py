"""Project and report path helpers."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

SHIPGATE_DIR = Path(".shipgate")
SHIPGATE_YAML = SHIPGATE_DIR / "shipgate.yaml"
PROJECT_CATALOG_DIR = SHIPGATE_DIR / "catalog"
PROJECT_CONFIGS_DIR = SHIPGATE_DIR / "configs"
PROJECT_GATES_DIR = SHIPGATE_DIR / "gates"
PROJECT_GATE_CONFIGS_DIR = PROJECT_CONFIGS_DIR / "gates"
PROJECT_CACHE_ENV = SHIPGATE_DIR / "cache" / ".env"
PROJECT_REPORTS_DIR = SHIPGATE_DIR / "reports"
PROJECT_REPORTS_RAW_DIR = PROJECT_REPORTS_DIR / "raw"
PROJECT_REPORTS_FAILURES_DIR = PROJECT_REPORTS_DIR / "failures"
PROJECT_TOOLS_DIR = SHIPGATE_DIR / "tools"
PROJECT_MANAGED_BIN_DIR = PROJECT_TOOLS_DIR / "bin"
PROJECT_MANAGED_PYTHON_ENV = PROJECT_TOOLS_DIR / "python"
PROJECT_SERVER_DIR = SHIPGATE_DIR / "server"
PROJECT_WORKTREES_DIR = SHIPGATE_DIR / "worktrees"
SERVER_DB_FILENAME = "report.db"
LEGACY_CONFIG_FILENAMES = ("shipgate.yaml", ".shipgate.yaml")
PROJECT_ROOT_CACHE_KEY = "SHIPGATE_ROOT"
POLICY_CACHE_KEY = "SHIPGATE_POLICY"
PROJECT_ENV_CACHE_KEY = "SHIPGATE_PROJECT_ENV"
RADON_CC_AVG_CACHE_ENV = "SHIPGATE_RADON_CC_AVG"
RADON_CC_MEDIAN_CACHE_ENV = "SHIPGATE_RADON_CC_MEDIAN"
RADON_CC_MAX_CACHE_ENV = "SHIPGATE_RADON_CC_MAX"
RADON_CC_P5_CACHE_ENV = "SHIPGATE_RADON_CC_P5"
RADON_CC_P10_CACHE_ENV = "SHIPGATE_RADON_CC_P10"
RADON_CC_P95_CACHE_ENV = "SHIPGATE_RADON_CC_P95"
RADON_MI_AVG_CACHE_ENV = "SHIPGATE_RADON_MI_AVG"
RADON_MI_MEDIAN_CACHE_ENV = "SHIPGATE_RADON_MI_MEDIAN"
RADON_MI_MIN_CACHE_ENV = "SHIPGATE_RADON_MI_MIN"
RADON_MI_P5_CACHE_ENV = "SHIPGATE_RADON_MI_P5"
RADON_MI_P10_CACHE_ENV = "SHIPGATE_RADON_MI_P10"
RADON_MI_P95_CACHE_ENV = "SHIPGATE_RADON_MI_P95"
ALLOWED_POLICY_VALUES = frozenset({"yaml", "pyproject"})


def project_gate_config_path(project_root: Path, gate_id: str) -> Path:
    gate_name = gate_id if gate_id.startswith("gate.") else f"gate.{gate_id}"
    return project_root / PROJECT_GATE_CONFIGS_DIR / f"{gate_name}.yaml"


def has_shipgate_yaml_config(candidate: Path) -> bool:
    return (
        True
        if (candidate / SHIPGATE_YAML).is_file()
        else any((candidate / name).is_file() for name in LEGACY_CONFIG_FILENAMES)
    )


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal KEY=VALUE env file."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def read_cached_policy(env_path: Path) -> str | None:
    """Return SHIPGATE_POLICY from cache when valid."""
    if not env_path.is_file():
        return None
    raw = parse_env_file(env_path).get(POLICY_CACHE_KEY)
    return raw if raw in ALLOWED_POLICY_VALUES else None


def update_project_cache_env(project_root: Path, updates: Mapping[str, str]) -> Path:
    """Merge keys into ``.shipgate/cache/.env``."""
    env_path = project_root / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True, exist_ok=True)
    values = parse_env_file(env_path) if env_path.is_file() else {}
    values |= {key: value for key, value in updates.items() if value}
    content = "".join(f"{key}={values[key]}\n" for key in sorted(values))
    env_path.write_text(content, encoding="utf-8")
    return env_path


def read_cached_project_root(env_path: Path) -> Path | None:
    """Return SHIPGATE_ROOT from cache when the path exists."""
    if not env_path.is_file():
        return None
    raw = parse_env_file(env_path).get(PROJECT_ROOT_CACHE_KEY)
    if not raw:
        return None
    root = Path(raw)
    if not root.is_dir():
        return None
    return root.resolve()


def find_cached_policy(start: Path) -> str | None:
    """Walk upward for `.shipgate/cache/.env` and return SHIPGATE_POLICY."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        policy = read_cached_policy(candidate / PROJECT_CACHE_ENV)
        if policy is not None:
            return policy
    return None


def find_cached_project_root(start: Path) -> Path | None:
    """Walk upward for `.shipgate/cache/.env` and return a valid cached root."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        cached = read_cached_project_root(candidate / PROJECT_CACHE_ENV)
        if cached is None:
            continue
        try:
            current.relative_to(cached)
        except ValueError:
            continue
        return cached
    return None


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward to find a project root.

    Precedence: cached ``SHIPGATE_ROOT`` (from ``shipgate init``), then
    ``.shipgate/shipgate.yaml``, legacy root YAML, ``.git``, or ``pyproject.toml``.
    """
    current = (start or Path.cwd()).resolve()
    cached = find_cached_project_root(current)
    if cached is not None:
        return cached
    for candidate in [current, *current.parents]:
        if has_shipgate_yaml_config(candidate):
            return candidate
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return current


def normalize_finding_path(
    path: str | None,
    *,
    project_root: Path | None = None,
) -> str | None:
    if not path:
        return None
    normalized = path.replace("\\", "/")
    if project_root is not None:
        with suppress(ValueError):
            rel = Path(normalized).resolve().relative_to(project_root.resolve())
            return rel.as_posix()
    return normalized[2:] if normalized.startswith("./") else normalized
