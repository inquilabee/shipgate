# Usage

Day-to-day suites, error formats, CI, and the report UI. First install? Start at
[Quick start](quickstart.md). Policy fields live in [Configuration](configuration.md).

## Mental model

- **Suite** — named checklist (`standard`, `full`, `python-quality`, …)
- **Tool** — one catalog entry (`ruff.lint`, `bandit.scan`, …)
- **`check`** — report-only; should not rewrite files
- **`format`** — apply write/fix checks (formatters)
- **`install`** — install tools for the selected suite (`env: managed` →
  `.shipgate/tools/`)

Pick a suite once in project policy; run the same three commands everywhere.
Override with `--suite` only for one-offs.

## Common commands

```bash
shipgate install
shipgate format --target .
shipgate check --target .
shipgate check --check ruff.lint --target .
shipgate list suites
shipgate list tools
shipgate schema > failure-report.schema.json
```

### One tool, one file

```bash
shipgate check --check ruff.lint --target app.py --error-format compact
```

```text
app.py:1: error: F401 `os` imported but unused
app.py:3: error: E302 Expected 2 blank lines, found 1
```

### Suites and targets

```bash
shipgate check
shipgate check --suite security
shipgate check --target src
shipgate check --error-format github   # CI / PR annotations
shipgate check --changed-only          # incremental when policy allows
shipgate check --full-tree             # ignore changed-only / --since for this run
```

Exit `0` on a clean run. Failures are non-zero; stderr follows `error-format`.
Canonical JSON always lands under `.shipgate/reports/` regardless of format.

## Suites

| Suite | Use it for |
| --- | --- |
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
# Max coverage while developing ShipGate itself
suite: full
error-format: compact
```

Live names: `shipgate list suites`.

## Error formats

| Format | Role |
| --- | --- |
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

Add structural rules separately — see [Refactor](refactor.md#ci-and-pre-commit).

## Report UI

```bash
pip install 'shipgate[server]'
shipgate serve
shipgate serve --port 8765 --open
```

Default bind is loopback: open `http://127.0.0.1:8765/`. No unlock step.

Non-loopback hosts (`0.0.0.0`, a private network address, …) require
`SHIPGATE_UI_TOKEN` or serve refuses to start. Unlock once in the browser at
`/ui-token` (or send the token in the `X-ShipGate-UI-Token` header). Unlock sets
an opaque session cookie — the env secret is not stored in the cookie.

```bash
export SHIPGATE_UI_TOKEN='long-random-secret'
shipgate serve --host 0.0.0.0 --port 8765
```

Prefer HTTPS termination in front of non-loopback binds; the UI itself is plain
HTTP.

## Refactor

Structural Python rules ship in the same wheel but outside catalog suites:

```bash
shipgate refactor check .
shipgate refactor fix src
shipgate refactor list
```

See [Refactor](refactor.md).

## Project-local gates

Scaffold under `.shipgate/gates/` and extend the project catalog under
`.shipgate/catalog/` when the bundled catalog is not enough. See
[Tools — project extensions](tools.md#project-extensions) and
[Check flow](check-flow.md).

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
