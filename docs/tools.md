# Tools

What each bundled check id does, and how to add your own. First run? See
[Quick start](quickstart.md). Suite selection lives in [Usage](usage.md).

## List the catalog

```bash
shipgate list tools
shipgate list tools --tag security
shipgate list checks    # alias
```

Run one tool without changing project policy:

```bash
shipgate check --check ruff.lint --target src
shipgate check --check gitleaks.scan --target .
```

## Bundled tools

| Tool | Purpose |
| ----------------------------------------------------------- | -------------------------------------------------- |
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
| [ty](https://docs.astral.sh/ty/) | Astral static type checker for Python |
| [Vulture](https://github.com/jendrikseipp/vulture) | Dead Python code with high confidence |
| [yamlfmt](https://github.com/google/yamlfmt) | YAML formatter |
| [yamllint](https://yamllint.readthedocs.io/) | YAML syntax and style linter |

## Project extensions

When the bundled catalog is not enough:

- **Catalog overlays** — add or override tool YAML under `.shipgate/catalog/tools/`
  (use `extends:` to patch a bundled entry).
- **Suites** — define named checklists in `.shipgate/catalog/suites.yaml`.
- **Policy gates** — scaffold scripts under `.shipgate/gates/` and register them
  in the project catalog.

Tool configs live under `.shipgate/configs/`. Project-specific allowlists go in
`.shipgate/allowlists/`. See [Usage — project-local gates](usage.md#project-local-gates)
and [Check flow](check-flow.md) for how YAML becomes a check run.
