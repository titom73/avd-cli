# AVD CLI

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful command-line interface for processing Arista AVD (Arista Validated Designs) inventories and generating configurations, documentation, and ANTA tests using py-avd.

## 🌟 Features

- **Configuration Generation**: Generate device configurations from AVD inventory
- **Documentation**: Automatically generate network documentation
- **ANTA Tests**: Generate ANTA test files for network validation
- **Flexible Workflows**: Support for both full (eos_design + eos_cli_config_gen) and config-only workflows
- **Group Filtering**: Process specific device groups only
- **Beautiful Output**: Rich terminal formatting with progress indicators
- **Comprehensive Testing**: >80% test coverage with pytest

## 📋 Requirements

- Python 3.9 or higher
- UV package manager (recommended) or pip
- Valid Arista AVD inventory structure

## 🚀 Installation

### Using UV (Recommended)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/aristanetworks/avd-cli.git
cd avd-cli

# Install the package
uv sync
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/aristanetworks/avd-cli.git
cd avd-cli

# Install the package
pip install -e .
```

## 💻 Usage

### Basic Commands

```bash
# Display help
avd-cli --help

# Generate configurations and documentation
avd-cli generate -i ./inventory -o ./output

# Generate configurations only (skip documentation)
avd-cli generate -i ./inventory -o ./output --config-only

# Generate with ANTA tests
avd-cli generate -i ./inventory -o ./output --generate-tests

# Limit to specific groups
avd-cli generate -i ./inventory -o ./output -l spine -l leaf

# Validate inventory structure
avd-cli validate -i ./inventory

# Display inventory information
avd-cli info -i ./inventory
```

### Command Options

#### `generate` - Generate configurations and documentation

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -o, --output-path PATH          Output directory for generated files [required]
  -l, --limit-to-groups TEXT      Limit processing to specific groups (multiple)
  --config-only                   Generate configuration only (skip docs)
  --workflow [full|config-only]   Workflow type [default: full]
  --generate-tests                Generate ANTA tests
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

#### `validate` - Validate inventory structure

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

#### `info` - Display inventory information

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -f, --format [table|json|yaml]  Output format [default: table]
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

## 📁 Expected Inventory Structure

```
inventory/
├── group_vars/
│   ├── all.yml
│   ├── FABRIC.yml
│   ├── SPINES.yml
│   └── LEAFS.yml
├── host_vars/
│   ├── spine1.yml
│   ├── spine2.yml
│   ├── leaf1.yml
│   └── leaf2.yml
└── inventory.yml
```

## 🧪 Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks
make pre-commit-install
```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with coverage report
make coverage

# Run linting
make lint

# Run type checking
make type

# Run all checks (format, lint, type, test)
make check
```

### Available Make Targets

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
```

## 🏗️ Architecture

AVD CLI follows a layered architecture:

```
avd_cli/
├── cli/              # CLI interface (Click commands)
├── models/           # Data models and validation
├── logics/           # Business logic and processing
└── utils/            # Utility functions
```

For detailed architecture information, see [spec/tool-avd-cli-architecture.md](spec/tool-avd-cli-architecture.md).

## 📚 Documentation

- [Architecture Specification](spec/tool-avd-cli-architecture.md)
- [Workflow Processing](spec/process-avd-workflow.md)
- [Data Schema](spec/data-avd-inventory-schema.md)
- [Testing Strategy](spec/infrastructure-testing-strategy.md)

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests** for your changes
4. **Ensure all tests pass**: `make check`
5. **Commit your changes**: `git commit -m 'feat: add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Development Tools

#### Using Make (Recommended)

```bash
# Run all checks
make check

# Individual checks
make lint        # Linting
make type        # Type checking
make test        # Run tests
make coverage    # Coverage report
make format      # Format code
```

#### Using Tox (Alternative)

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
uv run tox -e py313     # Test on Python 3.13

# Run all default environments
uv run tox

# Using Makefile shortcuts
make tox-lint
make tox-type
make tox-test
make tox-all
```

### Code Quality Standards

- All code must pass linting (flake8, pylint)
- Type hints required for all public functions
- Test coverage must exceed 80%
- Follow NumPy-style docstrings
- Code must be formatted with black

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Arista Networks](https://www.arista.com/) for AVD
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [pytest](https://pytest.org/) for testing framework
