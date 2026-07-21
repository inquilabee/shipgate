# ShipGate ADR support

This file tracks the architecture decisions that support the main design document.

The complete current design lives in `docs/sdd.md`.

## Decision index

### ADR-001: keep policy separate from execution

Status: accepted

Project configuration describes repository intent. It does not describe command flags, recursion strategy, argument ordering, subprocess behavior, or installation paths.

Those details belong in the catalog and runtime.

### ADR-002: make Execution Request the internal API

Status: accepted

CLI, Python API, batch files, CI integrations, and future UI integrations should all produce the same Execution Request.

The runtime should not care how the request was initiated.

### ADR-003: model tools and suites as runnables

Status: accepted

Everything executable is a runnable.

A tool executes one external executable. A suite executes one or more runnables. This allows recursive groups such as `quality`, `security`, and `ci` without special execution paths.

### ADR-004: normalize output before formatting

Status: accepted

Tools may emit different native output formats, but ShipGate converts them into canonical ShipGate JSON before rendering final output.

Formatters consume canonical output only.

### ADR-005: keep the public plugin API private for now

Status: accepted

Catalog entries, bundled configurations, and normalizers are enough for the first implementation phase.

A public plugin API should wait until the internal catalog and normalizer contracts are stable.

### ADR-006: ship opinionated defaults

Status: accepted

ShipGate should be useful almost immediately after installation, similar to the default-first experience of tools like Trunk Code Quality.

A conventional repository should be able to run default workflows such as `shipgate`, `shipgate ci`, or `shipgate quality` without first writing a large project configuration file.

Project configuration exists to override policy and defaults, not to make the product usable.

### ADR-007: preserve the prior UX, replace the internals

Status: accepted

The earlier `inquilabee/shipgate` attempt is a useful product sketch. Its small command set, bundled checks, managed install flow, quiet success, and structured failure reports remain part of the product direction.

The new design exists because that attempt was not extensible enough. ShipGate should keep the user-facing goals while moving tool behavior, invocation, suite composition, and output conversion into declarative catalogs, Execution Requests, runnables, and normalizers.

### ADR-008: seed the catalog from the prior tool set

Status: accepted

The first broad bundled catalog should start from the useful tools in the earlier ShipGate attempt: Ruff, ty, Bandit, Semgrep, Gitleaks, codespell, deadcode, Vulture, Radon, pytest, mutmut, pydeps, markdownlint, mdformat, yamllint, yamlfmt, ShellCheck, shfmt, Hadolint, JSCPD, Sourcery, and project-local script gates.

Ruff remains the first vertical-slice tool. The rest should be added after the ruff path proves catalog loading, request planning, argv serialization, execution, normalization, and formatting.

### ADR-009: provide a SonarQube-inspired frontend

Status: accepted

The earlier attempt included a frontend inspired by SonarQube. ShipGate should still have a frontend for browsing runs, findings, reports, and quality gates.

The frontend must read canonical ShipGate reports rather than raw tool output. It should come after the CLI, report schema, report storage, and formatter contracts are stable.

## Decisions still open

- Project configuration schema
- Catalog schema
- Capability-to-check resolution
- Override and merge behavior
- Suite cycle and duplicate handling
- Parallel execution semantics
- Installation cache and lockfile model
- Canonical JSON schema versioning
