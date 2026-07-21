TARGETS := src tests docs

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
	uv run shipgate install --suite full
	uv run shipgate format --target .
	uv run shipgate format --check mdformat.apply --target .
	uv run shipgate format --check shfmt.apply --target .
	@for t in $(TARGETS); do uv run shipgate check --suite full --target $$t; done

install-hooks:
	uv run pre-commit install

.PHONY: check-commit format install-hooks ruff test unit
