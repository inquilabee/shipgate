TARGETS := src tests

test:
	uv run pytest tests/ -q

unit:
	uv run pytest tests/unit -q

format:
	uv run ruff format src tests

ruff:
	uv run ruff check src tests --fix

check-commit:
	uv run shipgate install
	@for t in $(TARGETS); do uv run shipgate format --target $$t; done
	@for t in $(TARGETS); do uv run shipgate check --suite pre-commit --target $$t; done

install-hooks:
	uv run pre-commit install

.PHONY: check-commit format install-hooks ruff test unit
