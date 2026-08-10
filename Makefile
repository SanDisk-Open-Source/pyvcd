.PHONY: lint
lint: lint-ruff lint-mypy

.PHONY: lint-ruff
lint-ruff:
	uv run --group lint ruff check
	uv run --group lint ruff format --check

.PHONY: lint-mypy
lint-mypy:
	uv run --group type mypy

.PHONY: lint-basedpyright
lint-basedpyright:
	uv run --group type basedpyright

.PHONY: format
format:
	uv run --group lint ruff format
	uv run --group lint ruff check --fix

.PHONY: test
test:
	uv run --group test pytest

.PHONY: coverage
coverage:
	uv run --group test pytest --cov

.PHONY: benchmark
benchmark:
	uv run --group test pytest -vvs -k test_execution_speed

.PHONY: docs
docs:
	$(MAKE) -C docs html SPHINXBUILD="uv run --group docs sphinx-build"

.PHONY: build
build:
	uv build

.PHONY: dist
dist:
	uv build
