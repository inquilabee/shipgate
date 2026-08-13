# Changelog

<!-- markdownlint-disable MD024 -->

## Unreleased

## v0.1.10

### Fixed

- Ignore leftover tool JSON unless this run wrote the output file.
- Contain install, git, pip, and config paths under the project root.
- Auto-mode refactor no longer rewrites aliases, async generators, or empty `len()`.
- Honor pyproject-only policy without merging leftover YAML; skip unsupported apply
  mode.
- Reject extra batch paths and treat invalid batch files as config errors.
- Walk GitHub download redirects hop by hop; refuse userinfo / off-site hosts
  before reading a body; open `.tar.xz` assets with xz.
- Refactor check/fix: skip only parse and I/O errors; do not read escaped
  check paths; stop gitignore walking at `.git` or `pyproject.toml`; stack
  nested `!` un-ignore patterns.
- Scope include `src` no longer matches `src_backup`; apply mode drops targets
  outside the project.
- Parallel fail-fast and cancel keep completed sibling reports.
- Map managed-venv failures to `InstallError`.
- Treat `[::1]` as loopback; non-loopback HTML can unlock via an HttpOnly
  UI-token cookie instead of embedding the secret in the page.

### Changed

- `ProjectConfigParser.parse` takes `dict[str, object]` (no `Any` cast).

## v0.1.9

### Fixed

- `shipgate.__version__` follows the installed package metadata (`pyproject.toml`),
  so it cannot drift from the published version.
- `import-linter.check` uses layout detection for an importable package (src or
  flat) instead of requiring `src/*/__init__.py`.

## v0.1.8

### Fixed

- Check-result cache keys now include scoped file contents and check bindings
  (threshold / metric extras), so `shipgate check` no longer replays stale
  failures after source or policy edits ([#1](https://github.com/inquilabee/shipgate/issues/1)).
- `delivery: dirs` no longer passes `.` when a named scope includes a root-level
  `.py` file, so vulture/deadcode/radon do not walk `.shipgate/tools`.
- Managed env prepends `src/` onto `PYTHONPATH` when `src/<pkg>/__init__.py`
  exists, so import-linter can import src-layout packages without a consumer
  `.pth` script.
- `deadcode.check` and `semgrep.scan` declare `install.requires_python: ">=3.11,<3.14"`
  and skip with that reason on Python 3.14 instead of `TOOL_EXIT`.
- Policy-gate gitignore patterns with a trailing slash now match the directory
  itself (`notes/` matches `notes`), so folder-breadth no longer scans ignored trees.

### Added

- Require-if skips print the missing glob to stderr (flat-layout import-linter
  is no longer silent). `no matching files in scope` stays quiet unless
  `--display-cli`.
- `shipgate radon reset` deletes progressive `SHIPGATE_RADON_*` keys from
  `.shipgate/cache/.env` so floors can re-seed after a refactor.

## v0.1.6

### Added

- Ship the `refactor` package in the same wheel as ShipGate, with inventory YAML
  package data and a `shipgate refactor` subcommand (check / fix / list / explain).
- MkDocs documentation site (`docs/`, `mkdocs.yml`) with usage, architecture, and
  catalog reference pages.
- Split refactor and catalog validation into focused modules for maintainability.

### Changed

- Drop the standalone `refactor` console script; use `shipgate refactor` (or
  `python -m refactor` for module invocation).

### Notes

- Dogfood `.shipgate/configs/ruff.toml` calibrations (libcst visitor naming,
  sqlite dynamic SQL) stay project-local; bundled defaults remain portable.

## v0.1.5

### Added

- Radon `p5` / `p10` metric gates (MI floors / CC ceilings), matching `p95`.
- On radon MI/CC metric-gate failure, emit distribution summary and worst-offender
  findings (canonical JSON; formatters stay tool-agnostic).
- `shipgate radon calibrate {mi|cc}` suggests median / p5 / p10 / p95 / min/max
  thresholds and a YAML binding snippet from a live scan or `--json-file`.

### Changed

- Bundled `shipgate init` radon.mi distribution floors are **progressive** (portable);
  dogfood keeps absolute median / `p5` / `p10` plus progressive `minimum`, and drops
  the inverted MI `p95≥100` floor.
- Split layout role/collapse helpers out of `LayoutEngine` to improve maintainability.

## v0.1.4

### Added

- Layout-aware `shipgate init` scopes: detects `python-src`, `python-test-src`,
  and `docs` from the project tree (pytest `testpaths` / markers preferred).
- Policy gate `gate.staticmethod-soup`: fails classes whose methods are only
  `@staticmethod` (pushes real instance methods or module functions).
- Catalog `require_if.files_present`: checks skip cleanly when prerequisites are
  missing (used by import-linter, deptry, and pip-audit on fresh trees).

### Changed

- `shipgate init` writes a minimal `pyproject.toml` when none exists so packaging
  tools have project metadata.
- Import-linter contracts are scaffolded only when an importable `src/<pkg>/`
  package exists (no more dirname-based fake `root_package`). Flat-layout
  packages are skipped until under `src/`.
- Deptry `known_first_party` is set only for an importable src package (not the
  pyproject project name alone).
- Deptry and related tools keep directory-root delivery under changed-only
  (`paths.aggregate: root`).

### Fixed

- Fresh-project `shipgate check --suite full` no longer TOOL_EXITs on
  import-linter / deptry / pip-audit when the tree has only loose `src/*.py`.

### Notes

- Pre-0.1.4 inits may still have a broken `.shipgate/configs/importlinter.ini`
  with a dirname `root_package`. Delete it and run `shipgate configs sync` once
  you have `src/<pkg>/__init__.py`.

## v0.1.3

### Added

- Bundled catalog tools: `pip-audit.audit`, `deptry.check`, and
  `import-linter.check` (wired into `security` / `extended` / `policy`, and thus
  `full`). `shipgate init` scaffolds import-linter contracts and a deptry
  pyproject starter.
- Optional Radon distribution gates for cyclomatic complexity and maintainability
  index: `average`, `median`, `minimum` / `maximum`, and `p95`, each with
  `threshold` or `progressive` mode. See `docs/usage.md`.

### Changed

- Dogfood Radon maintainability-index median floor raised to 55.8; Gitleaks
  allowlist covers ShipGate radon baseline env names.

## v0.1.2

### Fixed

- CLI argv normalization no longer drops arguments when `argv` is omitted.
- jscpd threshold breaches are classified as code findings, not tool failures,
  including repair of mis-stored UI rows on serve startup.

### Changed

- README quick-start now shows real check/format output and the report UI overview.

## v0.1.1

### Changed

- Rebuilt orchestrator line: policy under `.shipgate/`, Execution Request pipeline,
  catalog-driven tools/suites, and canonical reports under `.shipgate/reports/`.
- Public docs and GitHub Actions republished for the current package layout.

### Notes

- PyPI already had `0.1.0` from an earlier line; this release is **0.1.1**.
