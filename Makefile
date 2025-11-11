.PHONY: help install dev-install clean test lint type format check ci-lint ci-type ci-test coverage pre-commit run

help: ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	uv sync

dev-install: ## Install the package with dev dependencies
	uv sync --extra dev

clean: ## Clean build artifacts and cache files
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .tox .coverage coverage.json htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test: ## Run all tests
	uv run pytest tests/

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -m unit

test-integration: ## Run integration tests only
	uv run pytest tests/integration/ -m integration

test-e2e: ## Run end-to-end tests only
	uv run pytest tests/e2e/ -m e2e

lint: ## Run linting (flake8, pylint)
	uv run flake8 avd_cli tests
	uv run pylint avd_cli tests

type: ## Run type checking (mypy)
	uv run mypy avd_cli

format: ## Format code with black and isort
	uv run black avd_cli tests
	uv run isort avd_cli tests

check: format lint type test ## Run all checks (format, lint, type, test)

ci-lint: ## Run linting for CI (no fixing)
	uv run flake8 avd_cli tests
	uv run pylint avd_cli tests --fail-under=9.0

ci-type: ## Run type checking for CI
	uv run mypy avd_cli --strict

ci-test: ## Run tests for CI with coverage
	uv run pytest tests/ --cov=avd_cli --cov-report=term-missing --cov-report=json --cov-branch --cov-fail-under=80

coverage: ## Generate coverage report
	uv run pytest tests/ --cov=avd_cli --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

run: ## Run the CLI (example: make run ARGS="--help")
	uv run avd-cli $(ARGS)

build: ## Build the package
	uv build

publish-test: build ## Publish to TestPyPI
	uv publish --repository testpypi

publish: build ## Publish to PyPI
	uv publish

tox-list: ## List all tox environments
	uv run tox list

tox-lint: ## Run tox lint environment
	uv run tox -e lint

tox-type: ## Run tox type environment
	uv run tox -e type

tox-test: ## Run tox test environment
	uv run tox -e test

tox-all: ## Run all tox environments
	uv run tox

################################################################################
# Documentation targets
################################################################################

.PHONY: docs-serve
docs-serve: ## Serve documentation locally (with live reload)
	@echo "Starting MkDocs server..."
	@echo "Access at: http://127.0.0.1:8000"
	uv run mkdocs serve --livereload

.PHONY: docs-build
docs-build: ## Build documentation (with strict mode)
	@echo "Building documentation..."
	uv run mkdocs build --strict --verbose --clean
	@echo "✓ Documentation built successfully in ./site/"

.PHONY: docs-test
docs-test: ## Test mike deployment locally (no push)
	@echo "Testing mike deployment..."
	uv run mike deploy test-build test
	@echo "✓ Mike test successful (commit not pushed)"
	uv run mike list
	@echo ""
	@echo "⚠️  To undo the local commit: git reset --soft HEAD~1"

.PHONY: docs-list
docs-list: ## List all deployed documentation versions
	@echo "Deployed documentation versions:"
	uv run mike list

.PHONY: docs-deploy-dev
docs-deploy-dev: ## Deploy development documentation (main)
	@echo "Deploying development documentation..."
	uv run mike deploy --push main development
	@echo "✓ Development documentation deployed"

.PHONY: docs-deploy-stable
docs-deploy-stable: ## Deploy stable documentation (requires VERSION var)
ifndef VERSION
	@echo "Error: VERSION variable is required"
	@echo "Usage: make docs-deploy-stable VERSION=v0.1.0"
	@exit 1
endif
	@echo "Deploying stable documentation for $(VERSION)..."
	uv run mike deploy --push $(VERSION) stable
	uv run mike set-default --push stable
	@echo "✓ Stable documentation deployed for $(VERSION)"

.PHONY: docs-delete
docs-delete: ## Delete a documentation version (requires VERSION var)
ifndef VERSION
	@echo "Error: VERSION variable is required"
	@echo "Usage: make docs-delete VERSION=v0.1.0"
	@exit 1
endif
	@echo "Deleting documentation version $(VERSION)..."
	@read -p "Are you sure? [y/N]: " confirm && [ "$$confirm" = "y" ]
	uv run mike delete --push $(VERSION)
	@echo "✓ Documentation version $(VERSION) deleted"

.PHONY: docs-clean
docs-clean: ## Clean built documentation
	@echo "Cleaning documentation build..."
	rm -rf site/
	@echo "✓ Documentation build cleaned"

.PHONY: install-doc
install-doc: ## Install documentation dependencies
	@echo "Installing documentation dependencies..."
	uv sync --extra doc
	@echo "✓ Documentation dependencies installed"
