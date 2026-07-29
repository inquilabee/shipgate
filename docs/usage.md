# ShipGate usage guide

Day-to-day commands, suites, and integration patterns. For policy files and
threshold bindings see [Configuration](configuration.md). For the bundled
catalog see [Tools](tools.md).

## Mental model

- **Suite** — named checklist (`standard`, `full`, `python-quality`, …)
- **Tool** — one catalog entry (`ruff.lint`, `bandit.scan`, …)
- **`check`** — report-only; should not rewrite files
- **`format`** — apply write/fix checks (formatters)
- **`install`** — install tools for the selected suite (`env: managed` →
  `.shipgate/tools/`)

Pick a suite once in project policy; run the same three commands everywhere.
Override with `--suite` only for one-offs.

## Commands

```bash
shipgate install
shipgate format
shipgate check
shipgate list suites
shipgate list tools
shipgate check --check ruff.lint --target .
shipgate schema > failure-report.schema.json
```

### Check examples

```bash
shipgate check --check ruff.lint --target app.py --error-format compact
```

```text
app.py:1: error: F401 `os` imported but unused
app.py:3: error: E302 Expected 2 blank lines, found 1
```

```bash
shipgate check
shipgate check --suite security
shipgate check --target src
shipgate check --error-format github   # CI / PR annotations
```

### Format

```bash
shipgate format --target .
```

## Suites

| Suite | Use it for |
| --------------------- | --------------------------------------------------------- |
| `python-quality` | Core Python lint + type check (`ruff.lint`, `ty.check`) |
| `format` | Formatter/autofix tools that write files |
| `security` | Bandit, Gitleaks, Semgrep, pip-audit |
| `extended` | Broader lint/metrics (codespell, radon, jscpd, deptry, …) |
| `standard` | `python-quality` baseline |
| `full` | `standard` + `security` + `extended` + `policy` |
| `docs` | Markdown/YAML doc checks |
| `shell` | ShellCheck + shfmt |
| `policy` | Bundled in-process policy gates + import-linter |
| `docker` | Hadolint |
| `ci` | `standard` + `security` + `policy` |
| `nightly` / `release` | Full coverage wrappers |
| `pre-commit` | Format + python-quality |

Examples:

```yaml
# Local Python repo
suite: python-quality
error-format: text
```

```yaml
# CI baseline with GitHub annotations
suite: standard
error-format: github
```

```yaml
# Max coverage while developing shipgate itself
suite: full
error-format: compact
```

List live names anytime: `shipgate list suites`.

## Error formats

| Format | Role |
| --------- | ------------------------------------------- |
| `json` | Pretty JSON report, including `report_path` |
| `log` | Timestamped finding lines |
| `text` | Bullet-style finding lines |
| `compact` | `src/app.py:42: error: E501 Line too long` |
| `github` | `::error file=…,title=…::…` annotations |

## Pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: shipgate-format
        name: shipgate format
        entry: shipgate format --target .
        language: system
        pass_filenames: false
      - id: shipgate-check
        name: shipgate check
        entry: shipgate check --target .
        language: system
        pass_filenames: false
```

```bash
pre-commit install
```

This repository's own dogfood hooks are richer (see `.pre-commit-config.yaml` and
`make install-hooks`).

## Report UI

```bash
pip install 'shipgate[server]'
shipgate serve
shipgate serve --port 8765 --open
```

Browse suite runs and findings at `http://127.0.0.1:8765/`.

## Refactor

Structural Python rules ship in the same wheel but outside catalog suites:

```bash
shipgate refactor check .
shipgate refactor fix src
shipgate refactor list
```

See [Refactor](refactor.md) for `explain`, `--strict`, optional packs, and
`python -m refactor`.

## Project-local gates

Scaffold under `.shipgate/gates/` and extend the project catalog under
`.shipgate/catalog/` when the bundled catalog is not enough. See
[Tools — project extensions](tools.md#project-extensions),
[Check flow](check-flow.md), and [Contributing](contributing.md).

## CI

```yaml
name: quality

on:
  pull_request:
  push:
    branches: [main]

jobs:
  shipgate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uvx shipgate install
      - run: uvx shipgate check
```

Set `error-format: github` in project policy for PR annotations.
