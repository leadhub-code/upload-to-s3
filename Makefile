python3=python3
venv_dir=venv

check: $(venv_dir)
	$(venv_dir)/bin/python -m pytest -vvv --tb=native tests

lint: $(venv_dir)
	$(venv_dir)/bin/flake8 . --count --statistics

wheel: $(venv_dir)
	mkdir dist
	$(venv_dir)/bin/pip wheel . -w dist --no-deps
	test -f dist/upload_to_s3-*-py3-none-any.whl

$(venv_dir): requirements-tests.txt
	$(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install -r requirements-tests.txt
	$(venv_dir)/bin/pip install -e .
	touch $(venv_dir)
