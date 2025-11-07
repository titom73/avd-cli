# Development Tools Guide

This document describes the development tools available for the avd-cli project.

## Package Management

The project uses **UV** as the primary package manager for speed and reliability.

### Installation

```bash
# Install dependencies
uv sync

# Install with development dependencies
uv sync --extra dev
```

## Testing Tools

### Make (Recommended)

The Makefile provides convenient shortcuts for all development tasks:

```bash
# Display all available commands
make help

# Quality checks
make lint        # Run linting (flake8, pylint)
make type        # Run type checking (mypy)
make format      # Format code (black, isort)
make check       # Run all checks

# Testing
make test        # Run all tests
make test-unit   # Run unit tests only
make coverage    # Generate coverage report

# Pre-commit
make pre-commit  # Run pre-commit hooks
make pre-commit-install  # Install pre-commit hooks
```

### Tox (Alternative / Multi-Python Testing)

Tox provides backward compatibility and allows testing across multiple Python versions.

#### Available Environments

| Environment | Description | Python Versions |
|------------|-------------|-----------------|
| `lint` | Run linting checks | Current |
| `type` | Run type checking | Current |
| `test` | Run all tests | Current |
| `py39` | Run tests on Python 3.9 | 3.9 |
| `py310` | Run tests on Python 3.10 | 3.10 |
| `py311` | Run tests on Python 3.11 | 3.11 |
| `py313` | Run tests on Python 3.13 | 3.13 |
| `coverage` | Run tests with coverage | Current |
| `clean` | Clean build artifacts | N/A |
| `format` | Format code | Current |
| `format-check` | Check code formatting | Current |
| `pre-commit` | Run pre-commit hooks | Current |
| `check` | Run all checks | Current |
| `ci-lint` | CI linting | Current |
| `ci-type` | CI type checking | Current |
| `ci-test` | CI testing | Current |
| `ci-all` | Run all CI checks | Current |

#### Basic Usage

```bash
# List all available environments
uv run tox list

# Run specific environment
uv run tox -e lint
uv run tox -e type
uv run tox -e test

# Run tests on specific Python version
uv run tox -e py39
uv run tox -e py310
uv run tox -e py311
uv run tox -e py313

# Run multiple environments
uv run tox -e lint,type,test

# Run all default environments
uv run tox

# Using Makefile shortcuts
make tox-list
make tox-lint
make tox-type
make tox-test
make tox-all
```

#### Testing Multiple Python Versions

To test across all supported Python versions, you need to have them installed:

```bash
# Using pyenv (recommended)
pyenv install 3.9.19
pyenv install 3.10.14
pyenv install 3.11.9
pyenv install 3.13.0

# Set local Python versions
pyenv local 3.13.0 3.11.9 3.10.14 3.9.19

# Run tests across all versions
uv run tox -e py39,py310,py311,py313
```

#### CI/CD Environments

Special environments for CI/CD pipelines with stricter requirements:

```bash
# CI linting (fails on warnings)
uv run tox -e ci-lint

# CI type checking (strict mode)
uv run tox -e ci-type

# CI testing (with coverage thresholds)
uv run tox -e ci-test

# Run all CI checks
uv run tox -e ci-all
```

## Code Quality Tools

### Linting

**flake8**: Style guide enforcement

```bash
uv run flake8 avd_cli tests
```

**pylint**: Code quality analysis

```bash
uv run pylint avd_cli tests
```

### Type Checking

**mypy**: Static type checking

```bash
uv run mypy avd_cli
```

### Formatting

**black**: Code formatting

```bash
uv run black avd_cli tests
```

**isort**: Import sorting

```bash
uv run isort avd_cli tests
```

## Pre-commit Hooks

The project uses pre-commit to run checks automatically before commits:

```bash
# Install hooks
make pre-commit-install

# Run manually
make pre-commit

# Run on specific files
uv run pre-commit run --files avd_cli/cli/main.py
```

## Testing

### Pytest

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/cli/test_main.py

# Run tests with coverage
uv run pytest --cov=avd_cli --cov-report=html

# Run tests matching pattern
uv run pytest -k "test_generate"

# Run tests with specific markers
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e
```

## Choosing Between Make and Tox

### Use Make When

- ✅ You want the fastest execution
- ✅ You're doing local development
- ✅ You trust your local Python environment
- ✅ You want simple, direct commands

### Use Tox When

- ✅ You need to test across multiple Python versions
- ✅ You want isolated environments
- ✅ You're preparing for CI/CD
- ✅ You want backward compatibility with existing workflows
- ✅ You need reproducible test environments

## Workflow Recommendations

### Daily Development Workflow

```bash
# 1. Pull latest changes
git pull

# 2. Sync dependencies
uv sync --extra dev

# 3. Create feature branch
git checkout -b feature/my-feature

# 4. Make changes and test frequently
make test        # Quick feedback

# 5. Before committing
make format      # Auto-format
make check       # All checks

# 6. Commit with conventional commits
git commit -m "feat: add amazing feature"

# 7. Optional: Test across Python versions
uv run tox -e py39,py310,py311,py313
```

### Before Creating a PR

```bash
# Full local CI simulation
make check
uv run tox -e ci-all

# Or using tox for multi-version testing
uv run tox
```

### Debugging Test Failures

```bash
# Run with verbose output
uv run pytest -vv

# Run with print statements visible
uv run pytest -s

# Run with debugger on failure
uv run pytest --pdb

# Run only failed tests from last run
uv run pytest --lf
```

## Troubleshooting

### "tox command not found"

```bash
# Reinstall dev dependencies
uv sync --extra dev
```

### "Virtual environment mismatch"

This warning can be ignored - tox creates its own virtual environments:

```
warning: `VIRTUAL_ENV=.tox/lint` does not match the project environment path `.venv`
```

### Tox environments are slow

```bash
# Clean tox cache
rm -rf .tox

# Or just use make for faster execution
make lint
make type
make test
```

### Python version not found

```bash
# Install missing Python versions with pyenv
pyenv install 3.9.19
pyenv install 3.10.14
pyenv install 3.11.9
pyenv install 3.13.0

# Set them as available
pyenv local 3.13.0 3.11.9 3.10.14 3.9.19
```

## Summary

- **Make**: Fast, direct, recommended for daily development
- **Tox**: Isolated, multi-version, recommended for pre-PR checks and CI/CD simulation
- **UV**: Fast package management, used by both Make and Tox
- **Pre-commit**: Automatic checks before commits

Both Make and Tox delegate to the same underlying tools (UV + pytest + mypy + flake8 + pylint), so you get consistent results regardless of which you choose.
