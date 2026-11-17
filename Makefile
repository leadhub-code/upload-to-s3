check:
	uv run pytest -vvv --tb=native tests

lint:
	uv run flake8 . --count --statistics

wheel:
	uv build
