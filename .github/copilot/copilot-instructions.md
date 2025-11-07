# GitHub Copilot Instructions - AVD CLI

## Priority Guidelines

When generating code for this repository:

1. **Version Compatibility**: Always detect and respect the exact versions of languages, frameworks, and libraries used in this project
2. **Context Files**: Prioritize patterns and standards defined in the .github/copilot directory
3. **Codebase Patterns**: When context files don't provide specific guidance, scan the codebase for established patterns
4. **Architectural Consistency**: Maintain our Layered architectural style and established boundaries
5. **Code Quality**: Prioritize maintainability, performance, security, accessibility, and testability in all generated code

## Technology Version Detection

Before generating code, scan the codebase to identify:

1. **Language Versions**: Detect the exact versions of programming languages in use
   - Python 3.9-3.13 support (as defined in .github/python-versions.json)
   - Use only Python features compatible with minimum version 3.9
   - Default development version: Python 3.13

2. **Framework Versions**: Identify the exact versions of all frameworks
   - Check pyproject.toml for dependency versions
   - UV package manager (version 0.5.1 as configured)
   - Respect version constraints when generating code

3. **Library Versions**: Note the exact versions of key libraries and dependencies
   - Click for CLI framework
   - Rich for terminal output formatting
   - py-avd for Arista AVD integration
   - pytest for testing
   - Generate code compatible with these specific versions

## Context Files

Prioritize the following files in .github directory (if they exist):

- **.github/instructions/python.instructions.md**: Python coding standards and conventions
- **.github/instructions/testing.instructions.md**: Testing guidelines using pytest
- **.github/instructions/arista-domain.instructions.md**: Arista EOS and CloudVision integration patterns
- **.github/instructions/devops-core-principles.instructions.md**: DevOps principles and DORA metrics
- **.github/instructions/github-actions-ci-cd-best-practices.instructions.md**: CI/CD pipeline standards

## Project Architecture

### Core Project Structure

This is a Python CLI application with the following architectural decisions:

- **CLI Framework**: Click library for command-line interface
- **Terminal Output**: Rich library for beautiful, formatted output
- **Package Manager**: UV for dependency management
- **Testing**: pytest with comprehensive coverage requirements (>80%)
- **Code Quality**: Enforced through pre-commit hooks (black, mypy, flake8, pylint)

### Expected Directory Structure

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
├── docs/                       # Documentation
├── pyproject.toml              # Project configuration
└── README.md
```

## Codebase Scanning Instructions

When context files don't provide specific guidance:

1. Identify similar files to the one being modified or created
2. Analyze patterns for:
   - Naming conventions (snake_case for functions/variables, PascalCase for classes)
   - Code organization (separation of CLI, models, logics)
   - Error handling (custom exceptions, proper error messages)
   - Logging approaches (structured logging with Rich console)
   - Documentation style (NumPy-style docstrings)
   - Testing patterns (pytest fixtures, parametrization, mocking)

3. Follow the most consistent patterns found in the codebase
4. When conflicting patterns exist, prioritize patterns in newer files or files with higher test coverage
5. Never introduce patterns not found in the existing codebase

## Code Quality Standards

### Maintainability

- Write self-documenting code with clear naming
- Follow snake_case for functions, variables, and modules
- Follow PascalCase for classes and exceptions
- Use type hints for all function parameters and return values
- Keep functions focused on single responsibilities
- Limit function complexity (cyclomatic complexity <10)
- Use pathlib.Path instead of string concatenation for file paths

### Performance

- Use async/await for I/O operations when appropriate
- Implement lazy evaluation with generators for large datasets
- Use context managers for resource management
- Cache expensive operations with functools.lru_cache
- Prefer list comprehensions over loops when appropriate

### Security

- Never hardcode sensitive information (tokens, passwords)
- Use environment variables for configuration
- Validate all user inputs before processing
- Sanitize file names and paths to prevent directory traversal
- Use parameterized queries and safe string formatting

### Accessibility

- Provide clear, actionable error messages
- Support keyboard navigation in interactive components
- Use Rich library's accessibility features
- Ensure output is readable in different terminal environments

### Testability

- Write testable code with dependency injection
- Separate pure functions from side effects
- Use pytest fixtures for test setup
- Mock external dependencies in unit tests
- Aim for >80% code coverage

## Documentation Requirements

### Docstring Format

Follow NumPy-style docstrings for all public functions and classes:

```python
def process_avd_inventory(
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

    Examples
    --------
    >>> result = process_avd_inventory(
    ...     Path("./inventory"),
    ...     limit_to_groups=["spine", "leaf"],
    ...     generate_tests=True
    ... )
    >>> print(f"Generated {len(result['configs'])} configurations")
    """
```

### Code Comments

- Document complex business logic and algorithms
- Explain non-obvious design decisions
- Use TODO comments for planned improvements
- Avoid obvious comments that restate the code

## Testing Approach

### Unit Testing

- Test all public functions and methods
- Use pytest fixtures for reusable test setup
- Parametrize tests for multiple input scenarios
- Mock external dependencies (file system, network calls)
- Test error conditions and edge cases

### Integration Testing

- Test CLI commands end-to-end
- Verify AVD integration workflows
- Test file generation and validation
- Use temporary directories for file operations

### Test Structure

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from rich.console import Console

from avd_cli.models.inventory import AvdInventory
from avd_cli.exceptions import InvalidInventoryError


class TestAvdInventory:
    """Test cases for AvdInventory class."""

    @pytest.fixture
    def sample_inventory_path(self, tmp_path: Path) -> Path:
        """Create a sample inventory structure."""
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()
        # Setup test inventory files
        return inventory_dir

    def test_load_valid_inventory(self, sample_inventory_path: Path) -> None:
        """Test loading a valid AVD inventory."""
        inventory = AvdInventory.load(sample_inventory_path)
        assert inventory.is_valid()

    @pytest.mark.parametrize("invalid_structure", [
        "missing_group_vars",
        "missing_host_vars",
        "invalid_yaml"
    ])
    def test_load_invalid_inventory(
        self,
        invalid_structure: str,
        tmp_path: Path
    ) -> None:
        """Test loading invalid inventory structures."""
        with pytest.raises(InvalidInventoryError):
            AvdInventory.load(tmp_path)
```

## Technology-Specific Guidelines

### Python Guidelines

- Use Python 3.9+ features but maintain compatibility with 3.9
- Follow PEP 8 style guidelines (enforced by black)
- Use type hints for all function signatures
- Prefer f-strings over .format() or % formatting
- Use dataclasses for simple data containers
- Implement **str** and **repr** methods for custom classes

### Click CLI Guidelines

- Use Click decorators for command definition
- Group related commands using click.Group
- Implement proper help text and descriptions
- Use click.option() with appropriate types and validation
- Support environment variables with envvar parameter
- Implement proper error handling with click.ClickException

```python
import click
from rich.console import Console
from pathlib import Path

console = Console()

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """AVD CLI - Generate configurations and documentation from AVD inventory."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    if verbose:
        console.print("[blue]Verbose mode enabled[/blue]")

@cli.command()
@click.option(
    '--inventory-path', '-i',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help='Path to AVD inventory directory'
)
@click.option(
    '--output-path', '-o',
    type=click.Path(path_type=Path),
    default=Path('./output'),
    help='Output directory for generated files'
)
@click.option(
    '--limit-to-groups',
    multiple=True,
    help='Limit processing to specific groups'
)
@click.pass_context
def generate(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Path,
    limit_to_groups: tuple[str, ...]
) -> None:
    """Generate AVD configurations and documentation."""
    try:
        # Implementation here
        console.print("[green]✓[/green] Generation completed successfully")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise click.ClickException(str(e))
```

### Rich Output Guidelines

- Use Rich Console for all output formatting
- Create themed output with consistent colors
- Use tables for structured data display
- Implement progress bars for long operations
- Use panels for important information blocks

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def display_inventory_summary(inventory_data: Dict[str, Any]) -> None:
    """Display inventory summary in formatted table."""
    table = Table(title="AVD Inventory Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Details", style="green")

    for category, items in inventory_data.items():
        table.add_row(
            category.title(),
            str(len(items)),
            ", ".join(items[:3]) + ("..." if len(items) > 3 else "")
        )

    console.print(table)

def show_progress_operation(operation_name: str) -> Progress:
    """Create a progress display for long operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )
```

### UV Package Manager Guidelines

- Use `uv sync` for installing dependencies
- Use `uv run` for executing Python scripts
- Manage dependencies in pyproject.toml
- Use development dependencies in [tool.uv.dev-dependencies]
- Lock dependencies with uv.lock file

## Version Control Guidelines

### Semantic Versioning

- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- Use conventional commits for automatic versioning
- Document breaking changes in CHANGELOG.md
- Tag releases with version numbers

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

## General Best Practices

### Error Handling

- Create custom exception classes for domain-specific errors
- Provide clear, actionable error messages
- Log errors with appropriate detail level
- Use Rich to format error output beautifully

```python
class AvdCliError(Exception):
    """Base exception for AVD CLI operations."""
    pass

class InvalidInventoryError(AvdCliError):
    """Raised when inventory structure is invalid."""
    pass

class ConfigurationGenerationError(AvdCliError):
    """Raised when configuration generation fails."""
    pass
```

### Logging Configuration

- Use Python's logging module with structured output
- Configure different log levels for different environments
- Use Rich's logging handler for beautiful console output

```python
import logging
from rich.logging import RichHandler

def setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### File Operations

- Use pathlib.Path for all file operations
- Implement proper error handling for file I/O
- Use context managers for file operations
- Validate file paths and permissions

```python
from pathlib import Path
from typing import Optional

def ensure_output_directory(output_path: Path) -> Path:
    """Ensure output directory exists and is writable."""
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        # Test write permissions
        test_file = output_path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return output_path
    except PermissionError:
        raise AvdCliError(f"No write permission for directory: {output_path}")
    except OSError as e:
        raise AvdCliError(f"Cannot create directory {output_path}: {e}")
```

## Project-Specific Guidance

### AVD Integration Patterns

- Use py-avd library for AVD operations
- Validate inventory structure before processing
- Support both eos_design + eos_cli_config_gen and eos_cli_config_gen only workflows
- Generate ANTA tests when requested
- Implement proper error handling for AVD operations

### CLI Command Structure

```
avd-cli
├── generate          # Generate configurations and documentation
├── validate          # Validate inventory structure
├── info              # Display inventory information
└── test              # Generate and run ANTA tests
```

### Configuration Management

- Support configuration through:
  - Command-line options
  - Environment variables
  - Configuration files (YAML/TOML)
- Use Click's configuration precedence
- Validate configuration before processing

Remember: Always prioritize consistency with existing code patterns over external best practices. Scan the codebase thoroughly before generating any code to understand the established conventions and architectural decisions.
