# Changelog

<!-- markdownlint-disable MD024 -->

## Unreleased

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
  package exists (no more dirname-based fake `root_package`).
- Deptry and related tools keep directory-root delivery under changed-only
  (`paths.aggregate: root`).

### Fixed

- Fresh-project `shipgate check --suite full` no longer TOOL_EXITs on
  import-linter / deptry / pip-audit when the tree has only loose `src/*.py`.

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
