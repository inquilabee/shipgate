# Contributing to shipgate

Thanks for helping improve the orchestrator. This guide is for people changing
**shipgate itself**, not for using it in an application repo. Quick start:
[README.md](README.md). Usage details: [docs/usage.md](docs/usage.md).
Maintainer index: [AGENTS.md](AGENTS.md).

## Development setup

```bash
uv sync --group dev
make install-hooks   # optional: pre-commit hook
make check-commit    # install suite tools, format, full dogfood check
make build
```

After changing `suite:` in `.shipgate/shipgate.yaml`, re-run `shipgate install` so the managed tool set matches.

Useful Make targets:

| Target | Purpose |
| --- | --- |
| `make install-hooks` | Install git pre-commit hooks |
| `make check-commit` | `shipgate install` → `format` → `check` (dogfood suite) |
| `make unit` | Deterministic unit tests |
| `make test` | Full pytest suite (excludes `@pytest.mark.ui` by default) |
| `make test-ui` | Playwright UI tests |
| `make build` | sdist + wheel |
| `make publish-check` | Build and sanity-check the wheel |
| `make docker-test` | Fresh-machine smoke (Docker; network for tool pins) |

Use Python **3.13** locally when running the full suite (Semgrep does not support 3.14 yet). Library `requires-python` remains `>=3.11,<3.15`.

Managed binary installs need `git`, `curl`, and (for npm-based tools) `nodejs`/`npm` on `PATH`. See `docker/Dockerfile`.

## Architecture (short)

Layers (one responsibility each):

```text
domain/ → config/ → catalog/ → planning/ → adapter/ → runtime/ → normalize/ → formatters/
                                                                         → app.py → cli.py
```

Bundled catalog:

```text
src/shipgate/catalog/bundled/catalog/tools/*.yaml
src/shipgate/catalog/bundled/catalog/suites.yaml
src/shipgate/catalog/bundled/configs/
```

Project overrides live under `.shipgate/catalog/`, `.shipgate/gates/`, `.shipgate/configs/`, and `.shipgate/allowlists/`.

See [docs/architecture.md](docs/architecture.md) and [docs/check-flow.md](docs/check-flow.md).

## Adding a tool

1. Add `src/shipgate/catalog/bundled/catalog/tools/<id>.yaml` with install metadata, CLI option mapping, normalizer, and modes.
2. Reference the tool id from `src/shipgate/catalog/bundled/catalog/suites.yaml` when it should run in a suite.
3. Add or extend a normalizer under `src/shipgate/normalize/` when the tool needs custom parsing.
4. Keep planner/adapter/executor free of tool-specific `if tool_id == …` branches — catalog metadata owns argv.

Consumers can also extend the catalog under `.shipgate/catalog/` without forking the package.

## Quality bar

ShipGate dogfoods itself with suite `full` from `.shipgate/shipgate.yaml`. Do not weaken thresholds, narrow scopes, or grow unexplained allowlists to go green. Fix findings on the branch. Never bypass hooks (`--no-verify`, `SKIP=…`).

Canonical local gate: `make check-commit`.

## License

By contributing, you agree that your contributions will be licensed under the
same terms as this repository (see `LICENSE`).
