# Configuration

Edit project policy after [Quick start](quickstart.md). Suites and CI live in
[Usage](usage.md).

## Try this

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
shipgate install --suite standard
shipgate check --suite extended
```

Success is exit `0` with little stderr. Failures write findings to stderr in
`error-format` and always store canonical JSON under `.shipgate/reports/`.

## Policy files

Policy lives in `.shipgate/shipgate.yaml` or `[tool.shipgate]` in `pyproject.toml`
(see `.shipgate/pyproject.toml.example` after init). `shipgate init` also scaffolds
`.shipgate/catalog/`, `.shipgate/gates/`, `.shipgate/configs/`, and cache metadata.

When layout detection finds an importable package (`src/<pkg>/` or flat `pkg/` at
the repo root), init may add an `importlinter.ini` starter and a `[tool.deptry]`
section if missing. Trees with no importable package skip `import-linter.check`
with a stderr line such as `no importable package in project layout`. Managed env
prepends `src/` onto `PYTHONPATH` only for that src-layout package; flat packages
at the repo root stay on the default path. `known_first_party` is filled only for
a real package — otherwise the commented placeholder stays.

If an older init left a broken `importlinter.ini` (`root_package` set to the
directory name), delete it and re-run `shipgate configs sync` after you have a
real package. pip-audit needs no project config file.

Path delivery respects `.gitignore` unless a scope sets `respect_gitignore: false`.

Python support: **3.11–3.14**. Prefer **3.13** when running suites that include
Semgrep or deadcode. On 3.14 those tools skip with `requires_python: >=3.11,<3.14`
instead of crashing.

## Key fields

| Field | Role |
| -------------- | ----------------------------------------------------- |
| `suite` | Default checklist (`standard`, `full`, `security`, …) |
| `env` | `managed` installs tools under `.shipgate/tools/` |
| `target` | Default path root for `check` / `format` |
| `error-format` | Stderr shape on failure (`compact`, `github`, …) |
| `configs.mode` | How bundled vs project configs are discovered (see below) |
| `checks` | Per-tool scopes, thresholds, and metric gates |

### `configs.mode`

Each catalog tool declares `configuration.discover` paths (for example ruff:
`.shipgate/configs/ruff.toml`, `.ruff.toml`, `pyproject.toml`). ShipGate passes
the first resolved path to the tool's `--config` flag (or equivalent).

| Mode | Behavior |
| ---- | -------- |
| `auto` (default) | Prefer **repo-native** configs (anything outside `.shipgate/configs/`). If the project already has `[tool.ruff]` in `pyproject.toml`, a root `.ruff.toml`, or similar, that wins over scaffolded `.shipgate/configs/*` from `shipgate init`. Fall back to scaffold, then bundled catalog defaults when nothing repo-native exists. |
| `repo` | Use catalog `discover` order as written — `.shipgate/configs/` first when present. |
| `bundled` | Always use the bundled catalog config; ignore project files. |

`pyproject.toml` counts as a discover match only when the tool's
`pyproject_section` exists (for ruff, `[tool.ruff]`). This keeps `auto` aligned
with tools the project already configured.

Override the project suite for one run with `--suite`. List live names:
`shipgate list suites`.

## Radon metric gates

Letter-rank `threshold` still gates each block (cyclomatic complexity) or file
(maintainability index). Optional numeric gates cover distribution summaries
computed from Radon JSON:

| Metric | Meaning | Prefer for gating? |
| --------------------- | ------------------------------------------ | ----------------------------------- |
| `average` | Arithmetic mean | Useful, but skewed by outliers |
| `median` | 50th percentile | Preferred central tendency (robust) |
| `minimum` / `maximum` | Worst single value | Strict; one outlier fails the gate |
| `p5` / `p10` | Left-tail percentiles | Preferred low-end floors for MI |
| `p95` | 95th percentile (inclusive linear interp.) | Preferred high-end tail for CC |

**Direction:** Maintainability index is worse when lower → floors for average,
median, minimum, `p5`, `p10`, and `p95`. Cyclomatic complexity is worse when
higher → ceilings for average, median, maximum, `p5`, `p10`, and `p95`.

Prefer **median** over average when you care about typical code. For MI, prefer
**`p5` / `p10` / `minimum` floors** to control the bad left tail; a high MI
`p95` floor (for example `100`) mostly measures how many near-perfect files you
have, not how bad the worst files are. For CC, prefer **`p95`** over raw
`maximum` when you want a hard high-end bound without letting a single block
fail the whole suite.

When a metric gate fails, ShipGate emits canonical findings with the distribution
summary (`n`, median, mean) and the worst offenders (lowest MI files / highest CC
blocks) so humans and agents can fix without re-running ad-hoc radon scripts.

| Tool | Typical keys | Worse when |
| ---------- | -------------------------------------------------------------------- | ----------------- |
| `radon.mi` | `median-*`, `p5-*`, `p10-*` (also `average-*`, `minimum-*`, `p95-*`) | lower (floors) |
| `radon.cc` | `median-*`, `p95-*` (also `average-*`, `maximum-*`, `p5-*`, `p10-*`) | higher (ceilings) |

Modes:

- `threshold` — absolute floor/ceiling; fails when the measured metric crosses it.
- `progressive` — must not regress vs the last saved value in
  `.shipgate/cache/.env`. First progressive run seeds the baseline and passes.

Bundled `shipgate init` scaffolds **progressive** MI distribution floors (seed on
first run, fail on regression) plus letter rank `B`. That stays portable across
repos; pin absolute floors with `shipgate radon calibrate` when you want dogfood-
style strictness. ShipGate's own `.shipgate/shipgate.yaml` uses absolute median /
`p5` / `p10` thresholds and progressive `minimum` — not an inverted MI `p95≥100`
floor.

Env keys (progressive only): `SHIPGATE_RADON_MI_AVG`, `SHIPGATE_RADON_MI_MEDIAN`,
`SHIPGATE_RADON_MI_MIN`, `SHIPGATE_RADON_MI_P5`, `SHIPGATE_RADON_MI_P10`,
`SHIPGATE_RADON_MI_P95`, `SHIPGATE_RADON_CC_AVG`, `SHIPGATE_RADON_CC_MEDIAN`,
`SHIPGATE_RADON_CC_MAX`, `SHIPGATE_RADON_CC_P5`, `SHIPGATE_RADON_CC_P10`,
`SHIPGATE_RADON_CC_P95`.

After a refactor that dipped then recovered, reset those keys and re-seed on the
next check. This is not the check-result cache under `.shipgate/cache/check-results/`.

```bash
shipgate radon reset
shipgate check --check radon.mi
shipgate check --check radon.cc
```

Use `shipgate radon calibrate` when you want absolute floors instead of
progressive baselines.

```yaml
# Bundled init (portable): progressive MI floors
checks:
  radon.mi:
    threshold: B
    median-mode: progressive
    p5-mode: progressive
    p10-mode: progressive
    minimum-mode: progressive
  radon.cc:
    threshold: B
    median-mode: threshold
    median-threshold: 3
    p95-mode: threshold
    p95-threshold: 7
```

```yaml
# Absolute MI floors after calibrate (ShipGate dogfood style)
checks:
  radon.mi:
    threshold: B
    median-mode: threshold
    median-threshold: 55.8
    p5-mode: threshold
    p5-threshold: 28
    p10-mode: threshold
    p10-threshold: 32
    minimum-mode: progressive
```

### Calibrate suggested thresholds

```bash
shipgate radon calibrate mi --path src --path tests
shipgate radon calibrate cc --path src --yaml
shipgate radon calibrate mi --json-file /tmp/radon-mi.json
```

`shipgate radon calibrate` prints the live distribution (`n`, mean/median/min/max,
`p5`/`p10`/`p95`), the worst offenders, and a YAML binding snippet with
passable suggested floors (MI) or ceilings (CC). Use `--yaml` for the snippet
only. Prefer `--json-file` in tests or offline; otherwise radon runs from the
managed tool env when present.

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
