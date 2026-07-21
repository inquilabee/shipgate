test:
	uv run pytest tests/ -q

unit:
	uv run pytest tests/unit -q

format:
	uv run ruff format src tests

ruff:
	uv run ruff check src tests --fix

check-commit:
	uv sync --group dev
	uv run shipgate install
	uv run shipgate format --target .
	uv run shipgate check --target .

install-hooks:
	uv run pre-commit install

.PHONY: check-commit format install-hooks ruff test unit
