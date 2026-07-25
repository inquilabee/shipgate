# Changelog

<!-- markdownlint-disable MD024 -->

## Unreleased

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
