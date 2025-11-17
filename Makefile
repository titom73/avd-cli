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

ci: ci-lint ci-type ci-test ## Run all CI checks

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

################################################################################
# Docker targets
################################################################################

.PHONY: docker-build docker-build-dev docker-run docker-version docker-info

docker-build: ## Build Docker image with git version (make docker-build [TAG=custom-tag])
	@echo "Building Docker image..."
	@GIT_VERSION=$$(git describe --tags --always --dirty 2>/dev/null || echo "dev"); \
	GIT_SHA=$$(git rev-parse HEAD 2>/dev/null || echo "unknown"); \
	BUILD_DATE=$$(date -u +'%Y-%m-%dT%H:%M:%SZ'); \
	IMAGE_TAG=$${TAG:-$$GIT_VERSION}; \
	echo "Version: $$GIT_VERSION"; \
	echo "Revision: $$GIT_SHA"; \
	echo "Build date: $$BUILD_DATE"; \
	echo "Image tag: $$IMAGE_TAG"; \
	docker build \
		--build-arg VERSION=$$GIT_VERSION \
		--build-arg REVISION=$$GIT_SHA \
		--build-arg BUILD_DATE=$$BUILD_DATE \
		-t avd-cli:$$IMAGE_TAG \
		-t avd-cli:latest \
		.
	@echo "✓ Docker image built successfully"
	@echo "  Tags: avd-cli:$$IMAGE_TAG, avd-cli:latest"

docker-build-dev: ## Build Docker image with 'dev' version
	@echo "Building Docker image (dev)..."
	@BUILD_DATE=$$(date -u +'%Y-%m-%dT%H:%M:%SZ'); \
	docker build \
		--build-arg VERSION=dev \
		--build-arg REVISION=dev \
		--build-arg BUILD_DATE=$$BUILD_DATE \
		-t avd-cli:dev \
		.
	@echo "✓ Docker image built: avd-cli:dev"

docker-run: ## Run Docker container (make docker-run ARGS="--help")
	docker run --rm -it avd-cli:latest $(ARGS)

docker-version: ## Show version info from Docker image
	@echo "Docker image version information:"
	@docker inspect avd-cli:latest --format='Version: {{index .Config.Labels "org.opencontainers.image.version"}}'
	@docker inspect avd-cli:latest --format='Revision: {{index .Config.Labels "org.opencontainers.image.revision"}}'
	@docker inspect avd-cli:latest --format='Build date: {{index .Config.Labels "org.opencontainers.image.created"}}'

docker-info: ## Show all labels from Docker image
	@echo "Docker image labels:"
	@docker inspect avd-cli:latest --format='{{json .Config.Labels}}' | jq .

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
docs-deploy-stable: ## Deploy stable documentation (requires VERSION var, optional: FORCE=true)
ifndef VERSION
	@echo "Error: VERSION variable is required"
	@echo "Usage: make docs-deploy-stable VERSION=v0.1.0"
	@echo "       make docs-deploy-stable VERSION=v0.1.0 FORCE=true  # Force push if diverged"
	@exit 1
endif
	@echo "Deploying stable documentation for $(VERSION)..."
ifdef FORCE
	@echo "⚠️  Force mode enabled - will overwrite remote gh-pages"
	uv run mike deploy --ignore-remote-status $(VERSION) stable
	uv run mike set-default --ignore-remote-status stable
	@echo "Pushing to gh-pages with force..."
	git push origin gh-pages --force
else
	uv run mike deploy --push $(VERSION) stable
	uv run mike set-default --push stable
endif
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
