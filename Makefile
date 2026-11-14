.ONESHELL:
SHELL := /bin/bash
PYTHONIOENCODING := utf-8

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	uv venv info

.PHONY: install
install:          ## Install the project and all dependency groups.
	$(MAKE) lock
	uv sync --all-groups

.PHONY: lock
lock:             ## Resolve and update uv.lock.
	uv lock

.PHONY: fmt
fmt:              ## Format code and apply safe lint fixes.
	uv run ruff format src/
	uv run ruff format tests/
	uv run ruff check src/ --fix
	uv run ruff check tests/ --fix
	$(MAKE) syncdocs

.PHONY: lint
lint:             ## Run Ruff and mypy static checks.
	uv run ruff check src/
	uv run ruff check tests/
	uv run ruff format --check src/
	uv run ruff format --check tests/
	uv run mypy

.PHONY: test
test: lint        ## Run tests and generate coverage reports.
	uv run pytest -v --cov-config .coveragerc --cov=src -l --tb=short --maxfail=1 tests/
	uv run coverage xml
	uv run coverage html

.PHONY: precommit
precommit:        ## Format, lint and test the project.
	$(MAKE) fmt
	$(MAKE) test

.PHONY: watch
watch:            ## Run tests on every change.
	ls **/**.py | entr uv run pytest -s -vvv -l --tb=long --maxfail=1 tests/

.PHONY: clean
clean:            ## Clean unused files and build artifacts.
	@find ./ -name '*.pyc' -exec rm -f {} \;
	@find ./ -name '__pycache__' -exec rm -rf {} \;
	@find ./ -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf site
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: build
build:            ## Build the source distribution and wheel.
	uv build

.PHONY: validate
validate: build   ## Check the built distributions.
	uv run twine check dist/*

.PHONY: release
release:          ## Tag and push a release. Publishing runs in GitHub Actions.
	$(MAKE) precommit
	@echo "WARNING: This operation will create a version tag and push it to GitHub."

	@CURRENT_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
	@echo "Current (latest) Git tag: $$CURRENT_TAG"

	IFS=. read -r MAJOR MINOR PATCH <<< "$$CURRENT_TAG"
	@NEXT_PATCH_VERSION="$$MAJOR.$$MINOR.$$((PATCH + 1))"

	read -e -i "$$NEXT_PATCH_VERSION" -p "Enter the new release tag (e.g., 0.1.0, 1.0.0): " NEW_TAG

	echo "Creating git tag : $${NEW_TAG}"
	git tag "$${NEW_TAG}"
	git push -u origin HEAD --tags

	echo "GitHub Actions will build, validate and publish the release."

.PHONY: syncdocs
syncdocs:         ## Synchronize generated documentation.
	@echo "sync documentation ..."
	@uv run ./scripts/update_readme.py
	@uv run ./scripts/render_logo.py

.PHONY: logo
logo:             ## Render logo and favicon PNGs from their SVG sources.
	@uv run ./scripts/render_logo.py

.PHONY: docs
docs:             ## Build the documentation.
	$(MAKE) syncdocs
	@echo "building documentation ..."
	@rm -rf site
	@uv run --group docs sphinx-build -W --keep-going -b html docs site

.PHONY: linkcheck
linkcheck:        ## Check external documentation links.
	@uv run --group docs sphinx-build -b linkcheck docs site/linkcheck

.PHONY: tree
tree:             ## Show the project tree (excluding ignored folders).
	@uv run ./scripts/show_tree.py

.PHONY: pytree
pytree:           ## Show the project tree including source code.
	@uv run ./scripts/show_tree.py --show-code