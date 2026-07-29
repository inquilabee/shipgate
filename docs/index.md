---
hide:
  - navigation
  - toc
---

<div align="center" markdown>

![ShipGate banner](images/shipgate-banner.svg)

# ShipGate

Policy-first quality gates for Python projects.

One policy, one catalog, three commands — plus refactor. Linters, formatters,
scanners, metric gates, and structural Python rules without hand-rolled CI glue.

[Usage guide](usage.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/inquilabee/shipgate){ .md-button }

</div>

## Where to start

| You want… | Start here |
| -------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Install and run in minutes | [README on GitHub](https://github.com/inquilabee/shipgate/blob/main/README.md) — quick commands only |
| Suites, CI, error formats, gates | [Usage guide](usage.md) |
| Structural Python refactor rules | [Refactor](refactor.md) |
| Policy files and thresholds | [Configuration](configuration.md) |
| What each bundled tool does | [Tools](tools.md) |
| How ShipGate is built | [Architecture](architecture.md) |

The README stays short so you can copy-paste `init` / `install` / `format` /
`check` / `refactor` and move on. This site is the reference for everything else.

## Why ShipGate?

You start a Python project and quickly need a pile of tools — each with its own
config, install story, and CI glue. ShipGate replaces that sprawl with a single
policy file and a metadata-driven catalog.

```bash
shipgate install
shipgate format
shipgate check
shipgate refactor check .
```

Refactor is separate from catalog suites — see [Refactor](refactor.md).

## Built for real workflows

- **Ready by default** — opinionated suites, strict thresholds, and bundled
  configs; fix violations, don't weaken gates.
- **Agent-friendly** — pair with pre-commit so humans and AI agents hit the same
  gates on every commit.
- **Canonical reports** — structured JSON under `.shipgate/reports/` plus an
  optional report UI via `shipgate[server]`.
- **Extensible** — project-local catalog entries, policy gates, and managed tool
  installs under `.shipgate/tools/`.

## Try it in minutes

Install:

```bash
pip install shipgate
shipgate init
shipgate install
```

Check:

```bash
shipgate check --target .
```

Report UI:

```bash
pip install 'shipgate[server]'
shipgate serve --open
```

## Report UI

![ShipGate report UI](images/report-ui-overview.png)

Browse suite runs and findings at `http://127.0.0.1:8765/`.

## Learn more

| Guide | Contents |
| --------------------------------- | ----------------------------------------------------------- |
| [Usage](usage.md) | Commands, suites, error formats, CI, gates |
| [Refactor](refactor.md) | Structural Python rules (`check`, `fix`, `list`, `explain`) |
| [Configuration](configuration.md) | Policy, scopes, Radon metric gates |
| [Tools](tools.md) | Bundled catalog and extensions |
| [Architecture](architecture.md) | Layers and design decisions |
| [Check flow](check-flow.md) | Tool YAML → `shipgate check` |
| [Contributing](contributing.md) | Development setup for maintainers |
