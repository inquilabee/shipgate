## Configuration coverage notes

ShipGate should dogfood its own default catalog. The ShipGate repository must be able to run the standard bundled Python suite against itself and treat that run as the main proof that the defaults are usable.

The default tool set should be strong enough for serious Python development. It should catch formatting drift, lint errors, type problems, security issues, secrets, dead code, spelling mistakes, complexity risks, dependency problems, test failures, documentation issues, shell mistakes, Dockerfile issues, YAML issues, and repository-specific gates.

"Ready by default" does not mean loose or minimal. It means a Python repository can install ShipGate, select the default suite, and get a high-signal quality gate without first hand-tuning every tool.

The table below maps ShipGate's normalized options onto the starting tool set. Gaps marked `x` should be intentional tool limitations, not missing ShipGate design. If a default check cannot be configured, normalized, or reported cleanly, it is not ready for the standard suite yet.

| Tool | `PATHS` | `CONFIG` | `EXCLUDE` | `INCLUDE` | `FORMAT` | `OUTPUT` | `VERBOSE` | `QUIET` | `FIX` | `RULES` | `THRESHOLD` | `STDIN` | `EXIT_BEHAVIOR` |
| --------------- | ----- | --------------- | ----------- | --------------------- | ------------------ | ----------------------- | ----------- | ---------- | ----------------- | ------------------------------- | ----------------------------------------- | --------- | ------------- |
| bandit | ✓ | `--config` | `--exclude` | x | `--format` | `--output` | `-v` | `-q` | x | `--tests` / `--skip` | `--severity-level` / `--confidence-level` | x | `--exit-zero` |
| codespell | ✓ | x | `--skip` | x | x | x | `-v` | `-q` | `--write-changes` | `--builtin` / `--ignore-words*` | x | x | x |
| deadcode | ✓ | x | `--exclude` | x | `--json` | x | x | x | x | x | x | x | x |
| gitleaks-detect | ✓ | `--config` | x | x | `--report-format` | `--report-path` | `-v` | x | x | x | x | x | `--exit-code` |
| gitleaks-git | ✓ | `--config` | x | x | `--report-format` | `--report-path` | `-v` | x | x | x | x | x | `--exit-code` |
| hadolint | ✓ | `--config` | x | x | `--format` | `--file-path-in-report` | `-V` | x | x | `--ignore` | `--failure-threshold` | `-` | `--no-fail` |
| jscpd | ✓ | `--config` | `--ignore` | `--pattern` | `--reporters` | `--output` | `--verbose` | `--silent` | x | x | `--min-lines` / `--min-tokens` | x | `--threshold` |
| markdownlint | ✓ | `--config` | `--ignore` | x | `--json` | `--output` | x | x | `--fix` | `--enable` / `--disable` | x | `--stdin` | x |
| mdformat | ✓ | `--config` | x | x | x | x | x | x | (always formats) | x | x | `-` | `--check` |
| mutmut-run | ✓ | `--config` | x | x | x | x | x | x | x | x | x | x | x |
| mutmut-results | x | x | x | x | x | x | x | x | x | x | x | x | x |
| mutmut-show | x | x | x | x | x | x | x | x | x | x | x | x | x |
| mutmut-browse | x | x | x | x | x | x | x | x | x | x | x | x | x |
| pydeps | ✓ | x | x | x | x | `--output` | `-v` | x | x | x | `--max-bacon` | x | x |
| radon-cc | ✓ | x | `--exclude` | `--include-ipynb` | `--json` | x | x | x | x | x | `--min` / `--max` | x | x |
| radon-mi | ✓ | x | `--exclude` | `--include-ipynb` | `--json` | x | x | x | x | x | `--min` | x | x |
| radon-hal | ✓ | x | `--exclude` | `--include-ipynb` | `--json` | x | x | x | x | x | x | x | x |
| radon-raw | ✓ | x | `--exclude` | `--include-ipynb` | `--json` | x | x | x | x | x | x | x | x |
| ruff-check | ✓ | `--config` | `--exclude` | `--extend-include` | `--output-format` | `--output-file` | `-v` | `-q` | `--fix` | `--select` / `--ignore` | x | `-` | `--exit-zero` |
| ruff-format | ✓ | `--config` | `--exclude` | `--respect-gitignore` | x | x | `-v` | `-q` | (always formats) | x | x | `-` | `--check` |
| semgrep-scan | ✓ | `--config` | `--exclude` | `--include` | `--json` | `--output` | `--verbose` | `--quiet` | `--autofix` | `--config` | `--severity` | `-` | `--error` |
| shellcheck | ✓ | x | x | x | `--format` | x | `-V` | x | x | `--enable` / `--exclude` | `--severity` | `-` | x |
| shfmt-check | ✓ | x | x | x | x | x | x | x | x | x | x | `-` | `--diff` |
| shfmt-format | ✓ | x | x | x | x | x | x | x | `--write` | x | x | `-` | x |
| ty-check | ✓ | `--config` | x | x | `--output-format` | x | `-v` | `-q` | x | x | x | x | x |
| vulture | ✓ | x | `--exclude` | x | `--make-whitelist` | x | `-v` | x | x | x | `--min-confidence` | x | x |
| yamlfmt | ✓ | `--conf` | x | x | x | x | x | x | (always formats) | x | x | `-` | `--dry-run` |
| yamllint | ✓ | `--config-file` | `--ignore` | x | `--format` | x | x | `-q` | x | `--enable` / `--disable` | x | `-` | `--strict` |
