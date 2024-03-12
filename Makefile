python3=python3
venv_dir=venv

check: $(venv_dir)
	$(venv_dir)/bin/python -m pytest -vvv --tb=native tests

lint: $(venv_dir)
	$(venv_dir)/bin/flake8 . --count --statistics

$(venv_dir): requirements-tests.txt
	$(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install -r requirements-tests.txt
	$(venv_dir)/bin/pip install -e .
	touch $(venv_dir)
