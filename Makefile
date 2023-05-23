install: ## Install the poetry environment
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@(poetry env use $$(pyenv which python))
	@poetry install	--no-cache
	@poetry shell

format: ## Format code using isort and black.
	@echo "🚀 Formatting code: Running isort and black"
	@poetry run isort .
	@poetry run black .
	@echo "🚀 Deleting ipython notebook cell contents with nbstripout"
	@poetry run nbstripout notebooks/*

check: ## Check code formatting using isort, black, flake8 and mypy.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry lock --check"
	@poetry lock --check
	@echo "🚀 Checking code formatting: Running isort"
	@poetry run isort --check-only --diff .
	@echo "🚀 Checking code formatting: Running black"
	@poetry run black --check .
	@echo "🚀 Checking code formatting: Running flake8"
	@poetry run flake8 .


test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest --doctest-modules

build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build

clean-build: ## clean build artifacts
	@rm -rf dist

docs-test: ## Test if documentation can be built without warnings or errors
	@echo "🚀 Testing Docs"
	@poetry run mkdocs build -s

docs: ## Build and serve the documentation
	@echo "🚀 No docs to serve just yet"
	@poetry run mkdocs serve

.PHONY: docs

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help