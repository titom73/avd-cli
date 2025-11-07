# Contributing to AVD CLI

Thank you for your interest in contributing to AVD CLI! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- UV package manager (recommended) or pip
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/aristanetworks/avd-cli.git
cd avd-cli

# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks
make pre-commit-install
```

## 🧪 Running Tests

### Using Make (Recommended)

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests only

# Run with coverage report
make coverage

# Run linting
make lint

# Run type checking
make type

# Run all checks (format, lint, type, test)
make check
```

### Using Tox (Alternative)

The project supports tox for backward compatibility and testing across multiple Python versions:

```bash
# List all available environments
make tox-list
# or: uv run tox list

# Run specific environment
uv run tox -e lint      # Linting
uv run tox -e type      # Type checking
uv run tox -e test      # Run tests
uv run tox -e py39      # Test on Python 3.9
uv run tox -e py310     # Test on Python 3.10
uv run tox -e py311     # Test on Python 3.11
uv run tox -e py313     # Test on Python 3.13

# Run all default environments
uv run tox

# Using Makefile shortcuts
make tox-lint
make tox-type
make tox-test
make tox-all
```

## 📝 Code Quality Standards

### Linting and Formatting

All code must pass the following checks:

- **flake8**: PEP 8 compliance and code style
- **pylint**: Code quality and best practices (must score 10.00/10)
- **mypy**: Type checking (strict mode)
- **black**: Code formatting (120 char line length)
- **isort**: Import sorting

Run all checks:

```bash
make check
```

### Type Hints

Type hints are **required** for all functions and methods:

```python
from typing import Optional
from pathlib import Path

def process_inventory(
    inventory_path: Path,
    output_path: Path,
    limit_groups: Optional[list[str]] = None
) -> dict[str, Any]:
    """Process AVD inventory and return results."""
    pass
```

### Documentation

Use NumPy-style docstrings:

```python
def generate_config(hostname: str, inputs: dict[str, Any]) -> str:
    """Generate device configuration.

    Parameters
    ----------
    hostname : str
        Device hostname
    inputs : dict[str, Any]
        Device input variables

    Returns
    -------
    str
        Generated configuration

    Raises
    ------
    ConfigurationGenerationError
        If configuration generation fails
    """
    pass
```

### Test Coverage

- All new features must include tests
- Test coverage must be maintained above 80%
- Use pytest for all tests
- Follow AAA pattern (Arrange, Act, Assert)

```python
def test_load_inventory_success(tmp_path: Path) -> None:
    """Test successful inventory loading."""
    # Arrange
    inventory_path = tmp_path / "inventory"
    inventory_path.mkdir()
    (inventory_path / "inventory.yml").write_text("...")

    # Act
    loader = InventoryLoader()
    result = loader.load(inventory_path)

    # Assert
    assert result is not None
    assert len(result.get_all_devices()) > 0
```

## 🔧 Available Make Targets

```bash
make help                  # Display all available commands
make install              # Install the package
make dev-install          # Install with dev dependencies
make clean                # Clean build artifacts
make test                 # Run all tests
make test-unit            # Run unit tests only
make test-integration     # Run integration tests only
make test-e2e             # Run end-to-end tests only
make lint                 # Run linting
make type                 # Run type checking
make format               # Format code with black and isort
make check                # Run all checks
make coverage             # Generate coverage report
make pre-commit           # Run pre-commit hooks
make pre-commit-install   # Install pre-commit hooks
make tox-list             # List tox environments
make tox-lint             # Run tox lint environment
make tox-type             # Run tox type environment
make tox-test             # Run tox test environment
make tox-all              # Run all tox environments
```

## 🏗️ Architecture

AVD CLI follows a layered architecture:

```
avd_cli/
├── cli/              # CLI interface (Click commands)
│   └── main.py      # Command definitions and CLI entry point
├── models/           # Data models and validation
│   └── inventory.py # Inventory data structures
├── logics/           # Business logic and processing
│   ├── generator.py # Configuration/documentation generation
│   ├── loader.py    # Inventory loading
│   └── templating.py # Jinja2 template processing
└── utils/            # Utility functions
    └── schema.py    # Schema validation
```

### Key Design Principles

1. **Separation of Concerns**: CLI, business logic, and data models are separate
2. **Dependency Injection**: Pass dependencies through constructors
3. **Single Responsibility**: Each class/function has one clear purpose
4. **Type Safety**: Full type hints with mypy strict mode
5. **Testability**: Design for easy unit testing with mocks

For detailed architecture information, see [spec/tool-avd-cli-architecture.md](../spec/tool-avd-cli-architecture.md).

## 🔀 Git Workflow

### Branching Strategy

- `main` - Production-ready code
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(generator): add support for custom hardware platforms
fix(loader): handle missing group_vars directory gracefully
docs(readme): update installation instructions
test(loader): add tests for Jinja2 variable resolution
```

## 📋 Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests** for your changes
4. **Ensure all tests pass**: `make check`
5. **Update documentation** if needed
6. **Commit your changes**: `git commit -m 'feat: add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### PR Checklist

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes with 10/10 score (`make lint`)
- [ ] Type checking passes (`make type`)
- [ ] Test coverage maintained >80% (`make coverage`)
- [ ] Documentation updated
- [ ] Commit messages follow conventional commits
- [ ] CHANGELOG.md updated (for significant changes)

## 🐛 Reporting Issues

When reporting issues, please include:

1. **AVD CLI version**: `avd-cli --version`
2. **Python version**: `python --version`
3. **Operating system**
4. **Steps to reproduce**
5. **Expected behavior**
6. **Actual behavior**
7. **Error messages/logs** (with `--verbose` flag)
8. **Minimal reproducible example** (if possible)

## 💡 Feature Requests

Feature requests are welcome! Please:

1. Check existing issues to avoid duplicates
2. Clearly describe the use case
3. Explain why this feature would be useful
4. Provide examples if possible

## 📚 Documentation

### Code Documentation

- All modules must have module-level docstrings
- All public functions/classes must have docstrings
- Use NumPy-style docstrings for consistency
- Include examples in docstrings where helpful

### Project Documentation

Documentation is located in:

- `README.md` - User-facing documentation
- `docs/` - Detailed documentation and guides
- `spec/` - Architecture and design specifications

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## 🙏 Questions?

- Open an issue for questions
- Check existing documentation
- Review the architecture specification

Thank you for contributing to AVD CLI! 🎉
