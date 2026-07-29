test:
	uv run pytest tests/ -q

unit:
	uv run pytest tests/unit -q

test-ui:
	uv run playwright install chromium
	uv run pytest -m ui -q

format:
	uv run ruff format src tests

ruff:
	uv run ruff check src tests --fix

check-commit:
	uv sync --group dev
	uv run shipgate install
	uv run shipgate format --target .
	# src-layout: import-linter needs the package on PYTHONPATH in the managed tool env
	PYTHONPATH=src uv run shipgate check --target .
	# Commit gate: auto + hint (default check is auto-only)
	PYTHONPATH=src uv run python -m refactor check --strict src tests/refactor

install-hooks:
	uv run pre-commit install

build:
	uv build

docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

publish-check: build
	uv run python -c "import glob, zipfile, re; paths=sorted(glob.glob('dist/*.whl'), key=lambda p: [int(x) if x.isdigit() else x for x in re.findall(r'[0-9]+|[^0-9]+', p)]); assert paths, 'no wheel'; z=zipfile.ZipFile(paths[-1]); z.testzip(); print(paths[-1], 'ok')"

# Fresh-machine smoke test: empty project init/install/format/check, then optional repo dogfood.
# Requires Docker. Set SHIPGATE_DOCKER_DOGFOOD=0 to skip phase B.
DOCKER_IMAGE := shipgate-docker-test
docker-test: docker-test-staging
	docker build -f docker/Dockerfile -t $(DOCKER_IMAGE) .
	docker run --rm $(DOCKER_IMAGE)

docker-test-staging:
	scripts/docker-test/prepare-dogfood.sh

.PHONY: build check-commit docker-test docker-test-staging format install-hooks publish-check ruff test test-ui unit
