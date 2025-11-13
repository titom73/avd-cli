# AVD CLI - Claude Code Instructions

This document provides comprehensive guidance for working on the AVD CLI project with Claude Code. It synthesizes project specifications, coding standards, and best practices to enable effective AI-assisted development.

## Project Overview

**AVD CLI** is a Python-based command-line interface tool for processing Arista Ansible AVD (Arista Validated Designs) inventories and generating configurations, documentation, and ANTA tests using py-avd.

### Key Information

- **Language**: Python 3.9-3.13
- **Package Manager**: UV (modern Python package manager)
- **CLI Framework**: Click
- **Output Formatting**: Rich library
- **Testing**: pytest with >80% coverage requirement
- **Core Dependency**: py-avd library

### Project Structure

```
avd-cli/
├── avd_cli/                    # Main package
│   ├── __init__.py
│   ├── cli/                    # CLI commands and interfaces
│   ├── models/                 # Data models and domain objects
│   ├── logics/                 # Business logic and operations
│   ├── exceptions.py           # Custom exception classes
│   └── constants.py            # Project constants
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures and data
├── spec/                       # Comprehensive specifications
├── .github/                    # GitHub Actions, instructions, scripts
└── pyproject.toml              # Project configuration
```

## Core Architecture

### Layered Architecture Pattern

The project follows a **strict layered architecture**:

1. **CLI Layer** (`avd_cli/cli/`) - User interaction and input validation
2. **Logic Layer** (`avd_cli/logics/`) - Business logic and AVD processing
3. **Model Layer** (`avd_cli/models/`) - Data structures and validation

**Dependency Flow**: CLI → Logic → Models (never reverse)

### Command Group Structure

Commands are organized using Click's group functionality:

```bash
avd-cli [OPTIONS] COMMAND [ARGS]...

# Command groups
avd-cli generate SUBCOMMAND [OPTIONS]   # Generate group - configs, docs, tests
avd-cli deploy SUBCOMMAND [OPTIONS]     # Deploy group - configurations to devices
avd-cli validate [OPTIONS]              # Validate AVD inventory
avd-cli info [OPTIONS]                  # Display inventory information
avd-cli version                         # Version information
```

### Key Design Patterns

- **Command Pattern**: CLI command implementation
- **Strategy Pattern**: Different AVD workflow approaches (eos-design, cli-config)
- **Factory Pattern**: Creating AVD processor instances
- **Repository Pattern**: Inventory data access
- **Protocol Pattern**: Type-safe interfaces without inheritance

## Python Coding Standards

### UV Package Manager

**ALL commands must use UV**:

```bash
# Run tests
uv run pytest tests/

# Run linters
uv run flake8 avd_cli
uv run pylint avd_cli
uv run mypy --strict avd_cli

# Add dependencies
uv add package-name
uv add --dev dev-package-name
```

### Required Code Quality Standards

Code must pass ALL these checks:

- **black**: Code formatting
- **mypy --strict**: Type checking
- **flake8**: Linting
- **pylint**: Additional linting (score >= 9.0)
- **pytest**: >80% code coverage

### Type Hints

**MANDATORY** for all public functions:

```python
from pathlib import Path
from typing import Optional, List, Dict, Any

def process_inventory(
    inventory_path: Path,
    limit_to_groups: Optional[List[str]] = None,
    generate_tests: bool = False
) -> Dict[str, Any]:
    """Process AVD inventory and generate configurations.

    Parameters
    ----------
    inventory_path : Path
        Path to the AVD inventory directory
    limit_to_groups : Optional[List[str]], optional
        List of groups to limit processing to, by default None
    generate_tests : bool, optional
        Whether to generate ANTA tests, by default False

    Returns
    -------
    Dict[str, Any]
        Processing results including generated files and statistics

    Raises
    ------
    InvalidInventoryError
        If the inventory structure is invalid
    ConfigurationError
        If configuration generation fails
    """
```

### NumPy-Style Docstrings

**ALL public functions require comprehensive NumPy-style docstrings** with:

- Short description
- Parameters section with types
- Returns section with type
- Raises section for exceptions
- Examples section (when helpful)
- Notes section (when helpful)

### Lazy Imports for CLI Performance

**CRITICAL for CLI commands**: Use lazy imports for heavy dependencies to keep CLI startup fast (<100ms):

```python
# ✅ Good: Lazy imports in CLI commands
@click.command()
def generate_configs(inventory_path: Path, output_path: Path) -> None:
    """Generate configurations from inventory."""
    # Import heavy dependencies only when command runs
    from avd_cli.logics.generator import ConfigurationGenerator
    import pyavd

    # Command implementation...

# ❌ Bad: Top-level imports slow down ALL CLI operations
from avd_cli.logics.generator import ConfigurationGenerator
import pyavd  # Loads heavy dependency even for --help
```

**When to use lazy imports**:
- ✅ CLI commands loading heavy libraries (pyavd, etc.)
- ✅ Optional dependencies
- ✅ Modules with expensive initialization

**When NOT to use**:
- ❌ Core library modules
- ❌ Type checking imports (use `TYPE_CHECKING` guard)
- ❌ Standard library imports

### Path Handling

**Always use `pathlib.Path`**:

```python
from pathlib import Path

# ✅ Good: Using pathlib
def save_file(content: str, output_dir: Path, filename: str) -> Path:
    """Save file using pathlib."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(content, encoding='utf-8')
    return output_path

# ❌ Bad: String concatenation
def save_file_bad(content, output_dir, filename):
    output_path = output_dir + "/" + filename  # Path traversal risk
    with open(output_path, 'w') as f:
        f.write(content)
```

### Error Handling

**Use project-specific exceptions with clear messages**:

```python
from avd_cli.exceptions import (
    ValidationError,
    LoaderError,
    GeneratorError,
)

def load_inventory(inventory_path: Path) -> InventoryModel:
    """Load inventory with proper error handling."""
    try:
        with open(inventory_path) as f:
            data = yaml.safe_load(f)

        inventory = InventoryModel(**data)
        return inventory

    except FileNotFoundError as e:
        raise LoaderError(
            f"Inventory file not found: {inventory_path}"
        ) from e
    except yaml.YAMLError as e:
        raise LoaderError(
            f"Invalid YAML format in inventory: {e}"
        ) from e
```

### Logging

Use structured logging with Rich handler:

```python
import logging
from rich.logging import RichHandler

logger = logging.getLogger(__name__)

def generate_configs(inventory_path: Path, output_path: Path) -> None:
    """Generate configurations with proper logging."""
    logger.info(
        "Starting configuration generation",
        extra={
            "inventory_path": str(inventory_path),
            "output_path": str(output_path),
            "operation": "generation_start"
        }
    )

    try:
        result = generation_logic(inventory_path, output_path)

        logger.info(
            "Configuration generation completed",
            extra={
                "device_count": result.device_count,
                "operation": "generation_complete"
            }
        )
    except LoaderError as e:
        logger.error(
            "Configuration generation failed",
            extra={
                "error": str(e),
                "operation": "generation_failed"
            },
            exc_info=True
        )
        raise
```

## AVD-Specific Patterns

### Workflow Types

The CLI supports two distinct workflows:

**1. eos-design workflow** (default):
- Complete pipeline: fabric definitions → structured configs → CLI configs
- Executes eos_design + eos_cli_config_gen roles
- Use for: Greenfield deployments, full fabric automation

**2. cli-config workflow**:
- Direct: existing structured configs → CLI configs
- Executes eos_cli_config_gen role only
- Use for: Brownfield deployments, custom configs, faster iteration

### Default Output Directory

**IMPORTANT**: When `--output-path` is not specified, the CLI defaults to `<inventory_path>/intended/`:

```python
# Apply default output path if not provided
if output_path is None:
    output_path = inventory_path / "intended"
    console.print(f"[blue]ℹ[/blue] Using default output path: {output_path}")
```

This follows AVD best practices and community conventions.

### Environment Variables

**ALL CLI options support environment variables** with `AVD_CLI_` prefix:

```python
@click.option(
    '--inventory-path', '-i',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    envvar='AVD_CLI_INVENTORY_PATH',
    show_envvar=True,
    help='Path to AVD inventory directory'
)
```

Priority order:
1. Command-line arguments (highest)
2. Environment variables
3. Default values (lowest)

### Schema Constants from py-avd

Load platform names and device types dynamically from py-avd:

```python
from avd_cli.utils.schema import (
    get_supported_platforms,
    get_supported_device_types,
    get_avd_schema_version,
)

# Get dynamically loaded constants
platforms = get_supported_platforms()  # Falls back if py-avd unavailable
device_types = get_supported_device_types()
schema_version = get_avd_schema_version()
```

### Device Type Mapping

AVD uses device type aliases that map to canonical types:

| AVD Type | Canonical Type |
|----------|---------------|
| `l3spine` | `spine` |
| `l2leaf` | `leaf` |
| `l3leaf` | `leaf` |

Application must recognize and map these correctly.

### Directory-Based Variables

Support both file and directory formats for group_vars/host_vars:

```
inventory/
├── group_vars/
│   ├── all/                    # Directory with multiple files
│   │   ├── basics.yml
│   │   ├── aaa.yml
│   │   └── platform.yml
│   ├── FABRIC.yml              # Single file
│   └── SPINES/                 # Directory with multiple files
│       ├── topology.yml
│       └── bgp.yml
```

Files in directories are merged in **alphabetical order**, with later files overriding earlier ones.

### Jinja2 Template Support

AVD inventories use Jinja2 template syntax for variable references:

```yaml
# group_vars/SPINES.yml
l3spine:
  defaults:
    # Reference variable from hostvars
    platform: "{{ hostvars['spine01']['poc_platform'] }}"
    # Use filter with default value
    mtu: "{{ mlag_peer_link_mtu | default(9214) }}"
```

Template resolution must occur **after** all YAML files are loaded but **before** validation.

## Testing Requirements

### Coverage Requirements

- **Minimum**: 80% line coverage
- **Branch coverage**: Track and report
- **Critical paths**: 100% coverage (CLI commands, validation)

### Test Structure

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

class TestInventoryLoader:
    """Test cases for InventoryLoader class."""

    @pytest.fixture
    def loader(self) -> InventoryLoader:
        """Create inventory loader instance for testing."""
        return InventoryLoader()

    @pytest.fixture
    def sample_inventory_path(self, tmp_path: Path) -> Path:
        """Create sample inventory structure."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()
        # Setup minimal valid structure
        return inventory_dir

    def test_load_valid_inventory_success(
        self,
        loader: InventoryLoader,
        sample_inventory_path: Path
    ) -> None:
        """Test loading valid inventory succeeds.

        Given: Valid inventory directory structure
        When: load() is called
        Then: Inventory data is loaded without errors
        """
        # Arrange - done in fixtures

        # Act
        inventory = loader.load(sample_inventory_path)

        # Assert
        assert inventory is not None
        assert len(inventory.fabrics) > 0
```

### Test Patterns

- **AAA Pattern**: Arrange, Act, Assert
- **Parametrization**: Use `@pytest.mark.parametrize` for multiple cases
- **Mocking**: Mock external dependencies (py-avd, file system)
- **Fixtures**: Reusable test setup in `conftest.py`

### Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=avd_cli --cov-report=term-missing

# Run specific test markers
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not slow"

# Run with verbose output
uv run pytest -v tests/
```

## CLI Command Development

### Common Options Pattern

Extract common options to avoid duplication:

```python
def common_generate_options(func):
    """Common options for all generate subcommands."""
    func = click.option(
        '--inventory-path', '-i',
        type=click.Path(exists=True, file_okay=False, path_type=Path),
        required=True,
        envvar='AVD_CLI_INVENTORY_PATH',
        show_envvar=True,
        help='Path to AVD inventory directory'
    )(func)
    func = click.option(
        '--output-path', '-o',
        type=click.Path(path_type=Path),
        default=None,
        envvar='AVD_CLI_OUTPUT_PATH',
        show_envvar=True,
        help='Output directory (default: <inventory_path>/intended)'
    )(func)
    func = click.pass_context(func)
    return func

@generate.command('configs')
@common_generate_options
def generate_configs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path]
) -> None:
    """Generate device configurations."""
    # Apply default output path
    if output_path is None:
        output_path = inventory_path / "intended"
        console.print(f"[blue]ℹ[/blue] Using default output path: {output_path}")
```

### Rich Output Formatting

Use Rich for consistent, beautiful output:

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def display_generation_summary(
    category: str,
    count: int,
    output_path: Path
) -> None:
    """Display generation summary in table format."""
    table = Table(title="Generated Files")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Output Path", style="green")
    table.add_row(category, str(count), str(output_path))

    console.print("\n")
    console.print(table)
```

### Progress Tracking

Display progress for operations >2 seconds:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console
) as progress:
    task = progress.add_task(
        "[cyan]Generating configurations...",
        total=len(devices)
    )

    for device in devices:
        generate_device_config(device)
        progress.advance(task)
```

## Key Project Conventions

### File and Directory Conventions

- **Python modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Import Organization

```python
#!/usr/bin/env python
# coding: utf-8 -*-

"""Module docstring."""

# Standard library imports (alphabetically sorted)
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports (alphabetically sorted)
import click
from rich.console import Console

# Local application imports (alphabetically sorted)
from avd_cli.exceptions import ValidationError
from avd_cli.logics.generator import ConfigurationGenerator
```

### Commit Message Format

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `doc`, `ci`, `test`, `refactor`, `chore`, `bump`

**Scopes**: `eos_downloader`, `eos_downloader.cli`, or omit

### Version Management

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Python versions**: 3.9-3.13 (defined in `.github/python-versions.json`)
- **UV version**: 0.5.1 as configured

## Important Resources

### Specifications (spec/ directory)

- **tool-avd-cli-architecture.md**: Overall CLI architecture and design
- **data-avd-inventory-schema.md**: AVD inventory structure and validation
- **process-avd-workflow.md**: Workflow execution and state management
- **infrastructure-testing-strategy.md**: Testing approach and requirements
- **tool-deploy-eos-command.md**: Configuration deployment to EOS devices

### GitHub Instructions (.github/instructions/)

- **python.instructions.md**: Python coding standards
- **testing.instructions.md**: Testing guidelines
- **arista-domain.instructions.md**: Arista EOS and AVD domain knowledge
- **devops-core-principles.instructions.md**: DevOps and DORA metrics
- **github-actions-ci-cd-best-practices.instructions.md**: CI/CD patterns

### Key Files

- **pyproject.toml**: Project configuration and dependencies
- **.github/python-versions.json**: Source of truth for Python versions
- **.github/copilot/copilot-instructions.md**: GitHub Copilot guidance

## Common Pitfalls to Avoid

1. ❌ **Not using UV**: Always use `uv run` for commands
2. ❌ **Missing type hints**: All public functions need type annotations
3. ❌ **Missing docstrings**: NumPy-style docstrings are mandatory
4. ❌ **String path concatenation**: Use `pathlib.Path`
5. ❌ **Top-level heavy imports**: Use lazy imports in CLI commands
6. ❌ **Generic exceptions**: Use project-specific exception classes
7. ❌ **Hardcoded paths**: Use inventory-relative paths with defaults
8. ❌ **Ignoring environment variables**: Support `AVD_CLI_*` env vars
9. ❌ **Not showing env vars in help**: Use `show_envvar=True`
10. ❌ **Low test coverage**: Maintain >80% coverage

## Quick Reference Commands

```bash
# Development
uv run pytest tests/                    # Run tests
uv run pytest --cov=avd_cli            # Run with coverage
uv run black avd_cli/                  # Format code
uv run mypy --strict avd_cli/          # Type check
uv run flake8 avd_cli/                 # Lint
uv run pylint avd_cli/                 # Additional lint

# CLI Usage
uv run avd-cli generate all -i ./inventory
uv run avd-cli generate configs -i ./inventory -o ./output
uv run avd-cli deploy eos -i ./inventory --dry-run
uv run avd-cli validate -i ./inventory
uv run avd-cli info -i ./inventory

# Git
git commit -m "feat(scope): add feature"
git commit -m "fix: correct bug in validation"
```

## AI Assistant Reminders

When generating code for this project:

1. ✅ **Always check specifications first** - Refer to spec/ files for requirements
2. ✅ **Follow established patterns** - Look at existing code in the same layer
3. ✅ **Write tests alongside code** - Aim for >80% coverage
4. ✅ **Use type hints everywhere** - All public functions must have types
5. ✅ **Document thoroughly** - NumPy-style docstrings are mandatory
6. ✅ **Use lazy imports in CLI** - Keep CLI startup fast
7. ✅ **Support environment variables** - All options should have `envvar`
8. ✅ **Default to `intended/` output** - Follow AVD conventions
9. ✅ **Load constants from py-avd** - Don't hardcode platforms/device types
10. ✅ **Test with UV commands** - All test execution uses `uv run`

---

**Last Updated**: 2025-11-13
**Maintained By**: AVD CLI Development Team
**For Questions**: See spec/ directory or .github/instructions/
