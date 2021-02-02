.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	rm -rf docs/auto_examples/
	rm -rf docs/_build

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	poetry run flake8 tom tests

test: ## run tests quickly with the default Python
	mkdir -p build
	poetry run pytest

test-all: ## run tests on every Python version with tox
	poetry run tox

coverage: ## check code coverage quickly with the default Python
	poetry run coverage run --source tom -m pytest
	poetry run coverage report -m
	poetry run coverage html
	poetry run $(BROWSER) htmlcov/index.html

# The next two task work only when venv ist activated (i.e. with `poetry shell`)
docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/tom.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ tom
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	cp -a docs/xsd docs/_build/html
	# $(BROWSER) docs/_build/html/index.html
	firefox docs/_build/html/index.html &

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	poetry publish

dist: clean ## builds source and wheel package
	poetry build

install: clean ## install the package to the active Python's site-packages
	poetry install

version-major:
	bump2version major

version-minor:
	bump2version minor
https://fahrweg.dbnetze.com/resource/blob/4359918/b61f2cef98cb6d0ba5080a06b0ccf94a/02_EVU-Schnittstelle-Download-3-data.pdf
