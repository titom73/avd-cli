# Contributing to AVD CLI

Thank you for your interest in contributing to AVD CLI! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

We welcome suggestions for new features or improvements. Please create an issue with:

- A clear description of the enhancement
- The motivation behind it
- Potential implementation approach (if you have one)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** following our coding standards
4. **Write or update tests** for your changes
5. **Ensure all tests pass**:

   ```bash
   make check
   ```

6. **Commit your changes** following our commit message convention
7. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request** against the `main` branch

## Development Setup

### Prerequisites

- Python 3.9 or higher
- UV package manager (recommended)
- Git

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/avd-cli.git
cd avd-cli

# Install dependencies
uv sync --extra dev

# Install pre-commit hooks
make pre-commit-install
```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Use NumPy-style docstrings
- Maximum line length: 120 characters

### Code Quality

All code must pass:

- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pylint**: Static analysis (score >= 9.0)
- **mypy**: Type checking

Run all checks:

```bash
make check
```

### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use pytest markers appropriately:
  - `@pytest.mark.unit` for unit tests
  - `@pytest.mark.integration` for integration tests
  - `@pytest.mark.e2e` for end-to-end tests
  - `@pytest.mark.slow` for tests that take >1 second

Run tests:

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage
make coverage
```

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(cli): add support for ANTA test generation

Add --generate-tests flag to generate command to create
ANTA test files from AVD inventory.

Closes #123
```

```
fix(validation): handle empty inventory directories

Previously crashed with AttributeError when inventory
directory was empty. Now raises clear InvalidInventoryError.

Fixes #456
```

## Project Structure

```
avd-cli/
├── avd_cli/              # Main package
│   ├── cli/              # CLI commands
│   ├── models/           # Data models
│   ├── logics/           # Business logic
│   └── utils/            # Utilities
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── fixtures/         # Test data
├── spec/                 # Specifications
└── docs/                 # Documentation
```

## Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer approval required
3. **Testing**: All tests must pass
4. **Documentation**: Update docs if needed
5. **Changelog**: Update CHANGELOG.md for user-facing changes

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Update specifications in `spec/` if changing architecture
- Update CHANGELOG.md following Keep a Changelog format

## Questions?

Feel free to:

- Open an issue for questions
- Start a discussion on GitHub Discussions
- Contact the maintainers

Thank you for contributing to AVD CLI! 🎉
