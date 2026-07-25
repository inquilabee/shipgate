# ShipGate usage guide

Consumer-facing details beyond the [README](../README.md) quick start.

## Mental model

- **Suite** — named checklist (`standard`, `full`, `python-quality`, …)
- **Tool** — one catalog entry (`ruff.lint`, `bandit.scan`, …)
- **`check`** — report-only; should not rewrite files
- **`format`** — apply write/fix checks (formatters)
- **`install`** — install tools for the selected suite (`env: managed` →
  `.shipgate/tools/`)

Pick a suite once in project policy; run the same three commands everywhere.
Override with `--suite` only for one-offs.

## Config

Policy lives in `.shipgate/shipgate.yaml` or `[tool.shipgate]` in `pyproject.toml`
(see `.shipgate/pyproject.toml.example` after init). `shipgate init` also scaffolds
`.shipgate/catalog/`, `.shipgate/gates/`, `.shipgate/configs/`, and cache metadata.

```yaml
# .shipgate/shipgate.yaml
suite: standard
env: managed
target: .
error-format: compact
configs:
  mode: auto
```

```bash
shipgate check --suite extended
shipgate install --suite standard
```

Path delivery respects `.gitignore`. Failures write canonical JSON under
`.shipgate/reports/`; `error-format` controls stderr only. Success is silent
(exit `0`).

Python support: **3.11–3.14**. Prefer **3.13** when running suites that include
Semgrep (Semgrep does not support 3.14 yet).

## Pre-commit

A minimal consumer hook (also shown in the README):

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

This repository’s own dogfood hooks are richer (see `.pre-commit-config.yaml` and
`make install-hooks`).

## Suites

| Suite | Use it for |
| --- | --- |
| `python-quality` | Core Python lint + type check (`ruff.lint`, `ty.check`) |
| `format` | Formatter/autofix tools that write files |
| `security` | Bandit, Gitleaks, Semgrep |
| `extended` | Broader lint/metrics (codespell, radon, jscpd, …) |
| `standard` | `python-quality` baseline |
| `full` | `standard` + `security` + `extended` + `policy` |
| `docs` | Markdown/YAML doc checks |
| `shell` | ShellCheck + shfmt |
| `policy` | Bundled in-process policy gates |
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
| --- | --- |
| `json` | Pretty JSON report, including `report_path` |
| `log` | Timestamped finding lines |
| `text` | Bullet-style finding lines |
| `compact` | `src/app.py:42: error: E501 Line too long` |
| `github` | `::error file=…,title=…::…` annotations |

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

## Report UI

```bash
pip install 'shipgate[server]'
shipgate serve
shipgate serve --port 8765 --open
```

## Project-local gates

Scaffold under `.shipgate/gates/` and extend the project catalog under
`.shipgate/catalog/` when the bundled catalog is not enough. See
[CONTRIBUTING.md](../CONTRIBUTING.md) and [AGENTS.md](../AGENTS.md).

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

## Bundled tools

| Tool | Purpose |
| --- | --- |
| [Bandit](https://bandit.readthedocs.io/) | Security issue scanner for Python |
| [codespell](https://github.com/codespell-project/codespell) | Common misspellings in text and code |
| [deadcode](https://github.com/alanedwardes/deadcode) | Unused Python code via static analysis |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning for git repositories |
| [Hadolint](https://github.com/hadolint/hadolint) | Dockerfile linter |
| [JSCPD](https://docs.jscpd.io/) | Copy/paste / duplication detector |
| [markdownlint](https://github.com/DavidAnson/markdownlint) | Markdown style linter |
| [mdformat](https://github.com/executablebooks/mdformat) | Markdown formatter |
| [pydeps](https://github.com/thebjorn/pydeps) | Python dependency graphs |
| Policy gates | Bundled in-process / project-local policy checks |
| [Radon](https://radon.readthedocs.io/) | Cyclomatic complexity and maintainability metrics |
| [Ruff](https://docs.astral.sh/ruff/) | Fast Python linter and formatter |
| [Semgrep](https://semgrep.dev/) | Pattern-based security and quality analysis |
| [ShellCheck](https://www.shellcheck.net/) | Static analysis for shell scripts |
| [shfmt](https://github.com/mvdan/sh) | Shell script formatter |
| [Sourcery](https://sourcery.ai/) | Automated Python review / refactor suggestions |
| [ty](https://docs.astral.sh/ty/) | Astral static type checker for Python |
| [Vulture](https://github.com/jendrikseipp/vulture) | Dead Python code with high confidence |
| [yamlfmt](https://github.com/google/yamlfmt) | YAML formatter |
| [yamllint](https://yamllint.readthedocs.io/) | YAML syntax and style linter |

Live catalog: `shipgate list tools`.
