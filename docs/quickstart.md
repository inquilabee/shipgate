# Quick start

Get a Python repo gated with the same commands you will use in CI and pre-commit.

Requires Python **3.11–3.14** (prefer **3.13**). On 3.14, Semgrep and deadcode
skip with an explicit `requires_python` message instead of crashing.

## Try this

```bash
pip install shipgate              # or: uv add --dev shipgate
shipgate init                     # scaffolds .shipgate/ (pick yaml or pyproject)
shipgate install                  # tools for the suite in project policy
shipgate format --target .        # write formatters
shipgate check --target .         # report-only quality gates
```

`shipgate init` is a group: use `shipgate init yaml` or `shipgate init pyproject`
when you want to choose the policy form explicitly.

Structural rules (separate from catalog suites):

```bash
shipgate refactor check .
```

Browse last reports (optional):

```bash
pip install 'shipgate[server]'
shipgate serve --open
```

## What you should see

| Command | Success | Failure |
| --- | --- | --- |
| `install` | Tools land under `.shipgate/tools/` for `env: managed` | Non-zero exit; stderr names the failed install |
| `format` / `check` | Exit `0`, little or no stderr | Non-zero exit; findings on stderr in your `error-format` |
| `check` (always) | Canonical JSON under `.shipgate/reports/` | Same path; fix findings, do not weaken thresholds to go green |
| `refactor check` | Exit `0` and `[]` (or empty hit list) on stdout | Exit `1` and indented JSON hits |
| `serve` on `127.0.0.1` | UI at `http://127.0.0.1:8765/` | Bind/port errors on stderr |

Compact findings look like:

```text
src/app.py:12: error: F401 `os` imported but unused
```

List what your install can run:

```bash
shipgate list suites
shipgate list tools
```

## Next

- Day-to-day suites, CI, pre-commit, and report UI unlock → [Usage](usage.md)
- Policy file fields and Radon gates → [Configuration](configuration.md)
- `refactor fix` / packs / `--strict` → [Refactor](refactor.md)
