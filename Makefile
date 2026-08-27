# Makefile for easy development workflows.
# See docs/development.md for docs.
# Note GitHub Actions call uv directly, not this Makefile.

.DEFAULT_GOAL := default

# Safe default for every dependency resolution invoked through this Makefile.
UV_EXCLUDE_NEWER ?= 14 days
export UV_EXCLUDE_NEWER

TRYSCRIPT_VERSION ?= 0.1.7

.PHONY: default install lint lint-check test test-python test-golden upgrade build sync-skill clean

default: install lint test

install:
	uv sync --all-extras --all-groups

lint:
	uv run python devtools/lint.py

# Check-only lint, matching CI (does not modify files).
lint-check:
	uv run python devtools/lint.py --check

test: test-python test-golden

test-python:
	uv run pytest

test-golden:
	NPM_CONFIG_IGNORE_SCRIPTS=true npx --yes tryscript@$(TRYSCRIPT_VERSION) run tests/tryscript/*.tryscript.md

upgrade:
	uv sync --upgrade --all-extras --all-groups

build: install
	uv build --no-build-isolation

sync-skill:
	uv run python -m deep_transcribe.skill_support --repository-root .

clean:
	-rm -rf dist/
	-rm -rf *.egg-info/
	-rm -rf .pytest_cache/
	-rm -rf .ruff_cache/
	-rm -rf .mypy_cache/
	-rm -rf .venv/
	-find . -type d -name "__pycache__" -exec rm -rf {} +
