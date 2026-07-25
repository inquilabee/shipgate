# shipgate

Quality gates for Python repos that developers can run locally, in CI, or hand to
an agent without inventing a new workflow each time.

`shipgate` gives you one project config, a bundled catalog of checks, quiet success, and structured failure reports. It is inspired by Trunk and pre-commit, but keeps the surface area small:

```bash
shipgate install
shipgate format
shipgate check
```

## Install

```bash
pip install shipgate
# or
uv add --dev shipgate
```

Requires Python 3.11–3.14. Local dogfood prefers **3.13** (Semgrep does not support 3.14 yet).

## 60-Second Setup

```bash
shipgate init            # writes .shipgate/shipgate.yaml (yaml mode)
# or: shipgate init pyproject   # merge [tool.shipgate] into pyproject.toml
shipgate install         # install tools needed by the suite
shipgate format          # apply formatter/autofix checks
shipgate check           # report-only quality checks
```

Policy lives under `.shipgate/` (for example `.shipgate/shipgate.yaml`) or in `[tool.shipgate]` in `pyproject.toml`. `shipgate init` also scaffolds `.shipgate/catalog/`, `.shipgate/gates/`, `.shipgate/configs/`, and cache metadata.

ShipGate respects `.gitignore` when resolving check paths. Failures exit `1`, write a canonical JSON report under `.shipgate/reports/`, and print findings through your configured `error-format`. Success is silent and exits `0`.

The `suite:` value is the project default. You do not need to repeat `--suite` on every command unless you want a one-off override.

## Mental Model

- **Suite**: a named checklist, such as `standard`, `full`, or `python-quality`.
- **Tool**: one catalog entry (for example `ruff.lint` or `bandit.scan`).
- **`check`**: report-only. It should not rewrite your files.
- **`format`**: applies write/fix checks, such as formatters.
- **`install`**: installs the tools needed by the selected suite (managed env under `.shipgate/tools/` when `env: managed`).

Most teams pick a suite once in project policy and run the same three commands everywhere.

## Config That Matters

```yaml
# .shipgate/shipgate.yaml
suite: standard
env: managed
target: .
error-format: compact
configs:
  mode: auto
```

Or the equivalent `[tool.shipgate]` table in `pyproject.toml` (see `.shipgate/pyproject.toml.example` after init).

```bash
shipgate check --suite extended
shipgate install --suite standard
```

## Suites

Suites are bundled starting points. They choose which tools run; path delivery still respects `.gitignore`.

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

## Error Output

On failure, shipgate writes the canonical JSON report under `.shipgate/reports/`. `error-format` only controls what is printed to stderr.

| Format | Example output |
| --- | --- |
| `json` | Pretty JSON report, including `report_path` |
| `log` | Timestamped finding lines |
| `text` | Bullet-style finding lines |
| `compact` | `src/app.py:42: error: E501 Line too long` |
| `github` | `::error file=…,title=…::…` annotations |

## Daily Commands

```bash
shipgate install
shipgate format
shipgate check
```

Inspect what is available:

```bash
shipgate list suites
shipgate list tools
```

Run a single tool:

```bash
shipgate check --check ruff.lint --target .
```

Export the failure report schema:

```bash
shipgate schema > failure-report.schema.json
```

## Report UI

Browse suite runs and findings in a local web UI:

```bash
pip install 'shipgate[server]'
shipgate serve
shipgate serve --port 8765 --open
```

## Project-Local Gates

Use gates when a repo needs a policy that is not covered by the bundled catalog.
Scaffold under `.shipgate/gates/` and extend the project catalog under
`.shipgate/catalog/`. See the [contributing guide](CONTRIBUTING.md) and
[AGENTS.md](AGENTS.md).

## CI

Minimal GitHub Actions job:

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

For GitHub PR annotations, set `error-format: github` in project policy.

## Contributing

See the [contributing guide](CONTRIBUTING.md) for local development.
Maintainers: [AGENTS.md](AGENTS.md).

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

List the live catalog anytime with `shipgate list tools`.

## License

See [`LICENSE`](LICENSE).
