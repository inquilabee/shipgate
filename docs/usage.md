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
That includes an `importlinter.ini` starter (root package auto-detected) and a
`[tool.deptry]` section in `pyproject.toml` when missing. Customize contracts and
`known_first_party` for your layout; pip-audit needs no project config file.

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

### Radon metric gates

Letter-rank `threshold` still gates each block (cyclomatic complexity) or file
(maintainability index). Optional numeric gates cover distribution summaries
computed from Radon JSON:

| Metric | Meaning | Prefer for gating? |
| --- | --- | --- |
| `average` | Arithmetic mean | Useful, but skewed by outliers |
| `median` | 50th percentile | Preferred central tendency (robust) |
| `minimum` / `maximum` | Worst single value | Strict; one outlier fails the gate |
| `p95` | 95th percentile (inclusive linear interp.) | Preferred tail vs raw min/max |

**Direction:** Maintainability index is worse when lower → floors for average, median,
minimum, and p95. Cyclomatic complexity is worse when higher → ceilings for average,
median, maximum, and p95.

Prefer **median** over average when you care about typical code, and **p95** over
min/max when you want a hard tail bound without letting a single file/block fail
the whole suite.

| Tool | Typical keys | Worse when |
| --- | --- | --- |
| `radon.mi` | `median-*`, `p95-*` (also `average-*`, `minimum-*`) | lower (floors) |
| `radon.cc` | `median-*`, `p95-*` (also `average-*`, `maximum-*`) | higher (ceilings) |

Modes:

- `threshold` — absolute floor/ceiling; fails when the measured metric crosses it.
- `progressive` — must not regress vs the last saved value in
  `.shipgate/cache/.env`. First progressive run seeds the baseline and passes.

ShipGate’s own dogfood uses **strict `threshold`** (median + p95), not
progressive.

Env keys (progressive only): `SHIPGATE_RADON_MI_AVG`, `SHIPGATE_RADON_MI_MEDIAN`,
`SHIPGATE_RADON_MI_MIN`, `SHIPGATE_RADON_MI_P95`, `SHIPGATE_RADON_CC_AVG`,
`SHIPGATE_RADON_CC_MEDIAN`, `SHIPGATE_RADON_CC_MAX`, `SHIPGATE_RADON_CC_P95`.

```yaml
checks:
  radon.mi:
    threshold: B
    median-mode: threshold
    median-threshold: 55.5
    p95-mode: threshold
    p95-threshold: 100
  radon.cc:
    threshold: B
    median-mode: threshold
    median-threshold: 3
    p95-mode: threshold
    p95-threshold: 7
```

Consumers may still use progressive or average/min/max:

```yaml
checks:
  radon.mi:
    threshold: B
    average-mode: progressive
    minimum-mode: threshold
    minimum-threshold: 20
  radon.cc:
    threshold: B
    average-mode: threshold
    average-threshold: 5
    maximum-mode: progressive
```

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
| [deptry](https://deptry.com/) | Missing / unused / misplaced declared dependencies |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret scanning for git repositories |
| [Hadolint](https://github.com/hadolint/hadolint) | Dockerfile linter |
| [import-linter](https://import-linter.readthedocs.io/) | Layer and forbidden-import contracts |
| [JSCPD](https://docs.jscpd.io/) | Copy/paste / duplication detector |
| [markdownlint](https://github.com/DavidAnson/markdownlint) | Markdown style linter |
| [mdformat](https://github.com/executablebooks/mdformat) | Markdown formatter |
| [pip-audit](https://github.com/pypa/pip-audit) | Dependency CVE / vulnerability audit |
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
