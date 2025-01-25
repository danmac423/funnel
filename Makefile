#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = funnel
PYTHON_VERSION = 3.13
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Run example server in examples/main.py
.PHONY: run_server
run_server:
	$(PYTHON_INTERPRETER) examples/main.py

## Install Python Dependencies
.PHONY: uv
uv:
	uv venv
	. .venv/bin/activate && uv pip install -e .

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using ruff and isort
.PHONY: lint
lint:
	ruff check

## Format source code with ruff
.PHONY: format
format:
	ruff format

## Run mypy
.PHONY: mypy
mypy:
	mypy .

## Run tests
.PHONY: test
test:
	$(PYTHON_INTERPRETER) -m pytest tests

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
