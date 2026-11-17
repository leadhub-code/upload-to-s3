check:
	uv run pytest -vvv --tb=native tests

lint:
	uv run ruff check
	uv run ruff format --check

wheel:
	uv build
