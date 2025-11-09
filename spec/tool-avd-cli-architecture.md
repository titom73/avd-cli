---
title: AVD CLI Tool Architecture Specification
version: 1.5
date_created: 2025-11-06
last_updated: 2025-11-09
owner: AVD CLI Development Team
tags: [tool, architecture, cli, python, avd, command-groups, environment-variables, workflow, default-output-path]
---

# Introduction

This specification defines the architecture, design patterns, and technical requirements for the AVD CLI tool - a Python-based command-line interface for processing Arista Ansible AVD inventories and generating configurations, documentation, and ANTA tests using py-avd.

## 1. Purpose & Scope

### Purpose

Define the architectural components, design patterns, and technical constraints for building a maintainable, testable, and extensible CLI tool for AVD inventory processing.

### Scope

- CLI interface design and command structure
- Core architectural layers and component boundaries
- Technology stack and framework integration patterns
- Error handling and logging strategies
- Configuration management approach

### Audience

- Development team implementing the AVD CLI
- AI coding assistants (GitHub Copilot)
- Code reviewers and maintainers
- Future contributors

### Assumptions

- Users have basic knowledge of Arista AVD and Ansible inventory structure
- Python 3.9+ is available in the target environment
- Users have valid access to AVD inventory files

## 2. Definitions

- **AVD**: Arista Validated Designs - Ansible collection for network automation
- **py-avd**: Python library providing AVD functionality
- **ANTA**: Arista Network Test Automation framework
- **CLI**: Command-Line Interface
- **eos_design**: AVD role for generating EOS configuration from design abstractions (fabric topology to structured configs)
- **eos_cli_config_gen**: AVD role for generating EOS CLI configurations from structured configs
- **eos-design workflow**: Complete pipeline executing eos_design followed by eos_cli_config_gen to generate configs from fabric definitions
- **cli-config workflow**: Direct configuration generation using eos_cli_config_gen only, consuming existing structured configurations from Ansible inventory
- **UV**: Modern Python package manager and tool runner
- **Click**: Python package for creating CLI applications
- **Rich**: Python library for rich text and beautiful formatting in the terminal
- **Structured Configuration**: YAML-based device configuration data consumed by eos_cli_config_gen

## 3. Requirements, Constraints & Guidelines

### Functional Requirements

- **REQ-001**: CLI shall support generating both configuration and documentation from AVD inventory
- **REQ-002**: CLI shall support generating configuration only (without documentation)
- **REQ-003**: CLI shall support limiting builds to specific host groups defined in AVD inventory
- **REQ-004**: CLI shall support eos-design workflow (eos_design + eos_cli_config_gen pipeline)
- **REQ-005**: CLI shall support cli-config workflow (eos_cli_config_gen only with existing Ansible inventory)
- **REQ-006**: CLI shall provide option to generate ANTA tests for anta_runner execution
- **REQ-007**: CLI shall support configurable paths for inputs and outputs
- **REQ-007.1**: CLI shall default output path to `<inventory_path>/intended` when not explicitly specified
- **REQ-008**: CLI shall provide meaningful error messages for invalid operations
- **REQ-009**: CLI shall display progress information for long-running operations
- **REQ-010**: CLI shall validate AVD inventory structure before processing
- **REQ-011**: CLI shall use command groups to organize related commands for extensibility
- **REQ-012**: CLI shall support generating specific output types independently (configs, docs, tests)
- **REQ-013**: CLI shall allow future extension with additional command groups and subcommands
- **REQ-014**: CLI shall provide consistent output formatting across all generate subcommands
- **REQ-015**: CLI shall support hiding pyavd deprecation warnings by default with option to show them
- **REQ-016**: CLI shall accept eos-design and cli-config as workflow values for backward compatibility and clarity

### Technical Requirements

- **TEC-001**: Application shall be implemented in Python 3.9+
- **TEC-002**: Application shall use Click library for CLI framework
- **TEC-003**: Application shall use Rich library for terminal output formatting
- **TEC-004**: Application shall use py-avd library for AVD operations
- **TEC-005**: Application shall use UV package manager for dependency management
- **TEC-006**: Application shall use pytest for testing with >80% code coverage
- **TEC-007**: Application shall use type hints for all public APIs
- **TEC-008**: Application shall follow NumPy-style docstring format
- **TEC-009**: Application shall pass black, mypy, flake8, and pylint validation
- **TEC-010**: Application shall use pathlib.Path for all file operations
- **TEC-011**: Application shall load schema constants (platforms, device types) from py-avd dynamically

### Quality Requirements

- **QUA-001**: Code coverage shall exceed 80% for all modules
- **QUA-002**: All public functions shall have comprehensive docstrings
- **QUA-003**: Cyclomatic complexity shall not exceed 10 per function
- **QUA-004**: Functions should not exceed 50 lines of code
- **QUA-005**: Modules should not exceed 500 lines of code
- **QUA-006**: All CLI commands shall have help text and examples

### Security Requirements

- **SEC-001**: Application shall NOT hardcode sensitive information
- **SEC-002**: Application shall support environment variables for configuration
- **SEC-003**: Application shall validate and sanitize all file paths
- **SEC-004**: Application shall implement proper error handling without exposing internal details
- **SEC-005**: Application shall log operations without exposing sensitive data

### Environment Variables Requirements

- **ENV-001**: CLI shall support loading all command options from environment variables
- **ENV-002**: Environment variables shall follow the naming convention `AVD_CLI_<OPTION_NAME>`
- **ENV-003**: Environment variables shall be displayed in command `--help` output
- **ENV-004**: Command-line arguments shall take precedence over environment variables
- **ENV-005**: Environment variable values shall be validated using the same rules as CLI arguments
- **ENV-006**: Boolean flags shall support both `true`/`false` and `1`/`0` values in environment variables
- **ENV-007**: Path-type environment variables shall support both absolute and relative paths
- **ENV-008**: Multiple-value options shall support comma-separated values in environment variables

### Performance Requirements

- **PER-001**: CLI response time for info/debug commands shall be <500ms
- **PER-002**: AVD inventory validation shall complete in <1 second for typical inventories
- **PER-003**: Configuration generation progress shall be displayed for operations >2 seconds
- **PER-004**: Application shall stream large file operations to avoid memory overflow

### Constraints

- **CON-001**: Must maintain compatibility with Python 3.9 as minimum version
- **CON-002**: Must use UV package manager (no pip/poetry/pipenv)
- **CON-003**: Must integrate with existing py-avd library APIs
- **CON-004**: Must follow Semantic Versioning for releases
- **CON-005**: Must use conventional commits for version control

### Guidelines

- **GUD-001**: Prefer composition over inheritance for component design
- **GUD-002**: Separate concerns: CLI interface, business logic, data access
- **GUD-003**: Use dependency injection for testability
- **GUD-004**: Implement single responsibility principle for all components
- **GUD-005**: Use lazy evaluation for resource-intensive operations
- **GUD-006**: Prefer explicit over implicit behavior
- **GUD-007**: Use context managers for resource management
- **GUD-008**: Load constants from py-avd schema to maintain agility and avoid hardcoded values
- **GUD-009**: Provide graceful fallback for constants when py-avd is unavailable or during testing
- **GUD-010**: Extract common functionality into utility functions to avoid code duplication
- **GUD-011**: Maintain consistent user experience across all CLI commands with unified output formatting
- **GUD-012**: Default output paths should follow AVD community best practices (use `intended/` subdirectory)
- **GUD-013**: Always display informational messages when using default values to improve user awareness

### Design Patterns

- **PAT-001**: Command Pattern for CLI command implementation
- **PAT-002**: Strategy Pattern for different AVD workflow approaches
- **PAT-003**: Factory Pattern for creating AVD processor instances
- **PAT-004**: Repository Pattern for inventory data access
- **PAT-005**: Builder Pattern for complex configuration construction
- **PAT-006**: Command Group Pattern for organizing related CLI commands hierarchically

## 4. Interfaces & Data Contracts

### CLI Command Structure

```bash
# Main command group
avd-cli [OPTIONS] COMMAND [ARGS]...

# Command groups and commands
avd-cli generate SUBCOMMAND [OPTIONS]   # Generate group - configurations, docs, tests
avd-cli validate [OPTIONS]              # Validate AVD inventory structure
avd-cli info [OPTIONS]                  # Display inventory information
avd-cli version                         # Display version information

# Generate subcommands (extensible)
avd-cli generate configs [OPTIONS]      # Generate device configurations
avd-cli generate docs [OPTIONS]         # Generate documentation
avd-cli generate tests [OPTIONS]        # Generate ANTA tests
avd-cli generate all [OPTIONS]          # Generate everything (default)
```

**Rationale for Command Groups:**
The CLI uses Click's group functionality to organize related commands under logical groups. The `generate` group contains subcommands for different generation tasks, providing:

- Clear command hierarchy and discoverability
- Extensibility for future generation types (e.g., `generate diagrams`, `generate reports`)
- Consistent user experience with other modern CLI tools
- Ability to add more command groups in the future (e.g., `deploy`, `test`, `sync`)

### Command Options Schema

#### Environment Variable Support

All CLI options support corresponding environment variables following the naming convention `AVD_CLI_<OPTION_NAME>` (uppercase, underscores for word separation).

**Priority Order:**

1. Command-line arguments (highest priority)
2. Environment variables
3. Default values (lowest priority)

**Default Output Directory Behavior:**

When the `--output-path` / `-o` option is not specified (either via CLI argument or environment variable), the CLI automatically creates an `intended` subdirectory within the inventory path for all generated outputs. This follows AVD best practices and aligns with the standard AVD directory structure.

- **Default location**: `<inventory_path>/intended/`
- **Structure within intended**:
  - `configs/` - Device configurations
  - `documentation/` - Fabric documentation
  - `tests/` - ANTA test catalogs and inventories

**Example default behavior**:

```bash
# With inventory at ./inventory/, outputs go to ./inventory/intended/
$ avd-cli generate all -i ./inventory

# Outputs:
# - ./inventory/intended/configs/
# - ./inventory/intended/documentation/
# - ./inventory/intended/tests/
```

**Environment Variable Mapping:**

| CLI Option | Environment Variable | Type | Default Value | Example |
|-----------|---------------------|------|---------------|---------|
| `--inventory-path`, `-i` | `AVD_CLI_INVENTORY_PATH` | Path | *(required)* | `/path/to/inventory` |
| `--output-path`, `-o` | `AVD_CLI_OUTPUT_PATH` | Path | `<inventory_path>/intended` | `/path/to/output` |
| `--limit-to-groups`, `-l` | `AVD_CLI_LIMIT_TO_GROUPS` | Comma-separated | *(none)* | `spine,leaf` |
| `--workflow` | `AVD_CLI_WORKFLOW` | Choice | `eos-design` | `eos-design` or `cli-config` |
| `--show-deprecation-warnings` | `AVD_CLI_SHOW_DEPRECATION_WARNINGS` | Boolean | `false` | `true`, `false`, `1`, `0` |
| `--test-type` | `AVD_CLI_TEST_TYPE` | Choice | `anta` | `anta` or `robot` |

**Help Text Display:**

Environment variables must be shown in the `--help` output for each option:

```bash
$ avd-cli generate configs --help
Usage: avd-cli generate configs [OPTIONS]

  Generate device configurations only.

Options:
  -i, --inventory-path PATH  Path to AVD inventory directory  [env var:
                             AVD_CLI_INVENTORY_PATH; required]
  -o, --output-path PATH     Output directory for generated files  [env var:
                             AVD_CLI_OUTPUT_PATH; default: <inventory_path>/intended]
  -l, --limit-to-groups TEXT Limit processing to specific groups (can be
                             used multiple times)  [env var:
                             AVD_CLI_LIMIT_TO_GROUPS]
  --workflow [eos-design|cli-config]
                             Workflow type: eos-design (eos_design +
                             eos_cli_config_gen) or cli-config (eos_cli_config_gen only)  [env var:
                             AVD_CLI_WORKFLOW; default: eos-design]
  --show-deprecation-warnings
                             Show pyavd deprecation warnings (hidden by
                             default)  [env var:
                             AVD_CLI_SHOW_DEPRECATION_WARNINGS]
  --help                     Show this message and exit.
```

#### Generate Command Group

```python
@click.group()
@click.pass_context
def generate(ctx: click.Context) -> None:
    """Generate configurations, documentation, and tests from AVD inventory.

    This command group provides subcommands for generating different types
    of outputs from Arista AVD inventories. Use subcommands to generate
    specific outputs or use 'all' to generate everything.

    Examples
    --------
    Generate all outputs (uses default output path <inventory>/intended):

        $ avd-cli generate all -i ./inventory

    Generate all outputs with custom output path:

        $ avd-cli generate all -i ./inventory -o ./custom-output

    Generate only configurations:

        $ avd-cli generate configs -i ./inventory

    Generate only ANTA tests with custom output:

        $ avd-cli generate tests -i ./inventory -o ./custom-output
    """
    pass

# Common options decorator for reuse across subcommands
def common_generate_options(func):
    """Common options for all generate subcommands.

    All options support environment variables with the prefix AVD_CLI_.
    Environment variables are automatically shown in --help output.
    Command-line arguments take precedence over environment variables.
    """
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
        help='Output directory for generated files (default: <inventory_path>/intended)'
    )(func)
    func = click.option(
        '--limit-to-groups', '-l',
        multiple=True,
        envvar='AVD_CLI_LIMIT_TO_GROUPS',
        show_envvar=True,
        help='Limit processing to specific groups (can be used multiple times). '
             'Use comma-separated values in environment variable: AVD_CLI_LIMIT_TO_GROUPS=spine,leaf'
    )(func)
    func = click.option(
        '--show-deprecation-warnings',
        is_flag=True,
        default=False,
        envvar='AVD_CLI_SHOW_DEPRECATION_WARNINGS',
        show_envvar=True,
        help='Show pyavd deprecation warnings (hidden by default)'
    )(func)
    func = click.pass_context(func)
    return func

# Utility functions for consistent CLI behavior
def suppress_pyavd_warnings(show_warnings: bool) -> None:
    """Suppress pyavd deprecation warnings unless explicitly requested."""
    if not show_warnings:
        import warnings
        warnings.filterwarnings("ignore", message=".*is deprecated.*", category=UserWarning)

def display_generation_summary(
    category: str,
    count: int,
    output_path: Path,
    subcategory: str = "configs"
) -> None:
    """Display a consistent summary table for generated files."""
    from rich.table import Table

    table = Table(title="Generated Files")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Output Path", style="green")
    table.add_row(category, str(count), str(output_path / subcategory))
    console.print("\n")
    console.print(table)

#### Generate All Subcommand
```python
@generate.command('all')
@common_generate_options
@click.option(
    '--workflow',
    type=click.Choice(['eos-design', 'cli-config'], case_sensitive=False),
    default='eos-design',
    envvar='AVD_CLI_WORKFLOW',
    show_envvar=True,
    help='Workflow type: eos-design (eos_design + eos_cli_config_gen) or cli-config (eos_cli_config_gen only)'
)
def generate_all(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple,
    workflow: str
) -> None:
    """Generate all outputs: configurations, documentation, and tests.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Parameters
    ----------
    inventory_path : Path
        Path to AVD inventory directory
    output_path : Optional[Path]
        Output directory. If None, defaults to <inventory_path>/intended
    limit_to_groups : tuple
        Groups to limit processing to
    workflow : str
        Workflow type (eos-design or cli-config)

    Workflow Modes:
    - eos-design: Complete pipeline (fabric definitions -> structured configs -> CLI configs)
    - cli-config: Direct generation (existing structured configs -> CLI configs)

    Implementation
    --------------
    ```python
    # Apply default output path if not provided
    if output_path is None:
        output_path = inventory_path / "intended"
        console.print(f"[blue]ℹ[/blue] Using default output path: {output_path}")
    ```
    """

#### Generate Configs Subcommand
```python
@generate.command('configs')
@common_generate_options
@click.option(
    '--workflow',
    type=click.Choice(['eos-design', 'cli-config'], case_sensitive=False),
    default='eos-design',
    envvar='AVD_CLI_WORKFLOW',
    show_envvar=True,
    help='Workflow type: eos-design (eos_design + eos_cli_config_gen) or cli-config (eos_cli_config_gen only)'
)
def generate_configs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple,
    workflow: str
) -> None:
    """Generate device configurations only.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Parameters
    ----------
    output_path : Optional[Path]
        Output directory. If None, defaults to <inventory_path>/intended

    Workflow Modes:
    - eos-design: Complete pipeline (fabric definitions -> structured configs -> CLI configs)
    - cli-config: Direct generation (existing structured configs -> CLI configs)
    """

#### Generate Docs Subcommand
```python
@generate.command('docs')
@common_generate_options
def generate_docs(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple
) -> None:
    """Generate documentation only.

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Parameters
    ----------
    output_path : Optional[Path]
        Output directory. If None, defaults to <inventory_path>/intended
    """

#### Generate Tests Subcommand
```python
@generate.command('tests')
@common_generate_options
@click.option(
    '--test-type',
    type=click.Choice(['anta', 'robot'], case_sensitive=False),
    default='anta',
    envvar='AVD_CLI_TEST_TYPE',
    show_envvar=True,
    help='Type of tests to generate'
)
def generate_tests(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    limit_to_groups: tuple,
    test_type: str
) -> None:
    """Generate test files (ANTA or Robot Framework).

    All options can be provided via environment variables with AVD_CLI_ prefix.
    Command-line arguments take precedence over environment variables.

    Parameters
    ----------
    output_path : Optional[Path]
        Output directory. If None, defaults to <inventory_path>/intended
    """
```

### Internal API Contracts

#### Inventory Processor Interface

```python
from typing import Protocol, List, Dict, Any, Optional
from pathlib import Path

class InventoryProcessor(Protocol):
    """Protocol for AVD inventory processing."""

    def validate(self, inventory_path: Path) -> bool:
        """Validate inventory structure.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        bool
            True if valid, False otherwise

        Raises
        ------
        InvalidInventoryError
            If inventory structure is invalid
        """
        ...

    def load(self, inventory_path: Path) -> Dict[str, Any]:
        """Load inventory data.

        Parameters
        ----------
        inventory_path : Path
            Path to inventory directory

        Returns
        -------
        Dict[str, Any]
            Loaded inventory data
        """
        ...

    def generate_configs(
        self,
        inventory_data: Dict[str, Any],
        output_path: Path,
        limit_to_groups: Optional[List[str]] = None
    ) -> List[Path]:
        """Generate configurations.

        Parameters
        ----------
        inventory_data : Dict[str, Any]
            Loaded inventory data
        output_path : Path
            Output directory
        limit_to_groups : Optional[List[str]]
            Groups to limit processing to

        Returns
        -------
        List[Path]
            List of generated configuration files
        """
        ...
```

### Configuration File Schema

```yaml
# avd-cli.yaml - Optional configuration file
inventory:
  path: ./inventory
  validate_on_load: true

output:
  path: ./intended  # Optional, defaults to <inventory_path>/intended if not specified
  create_if_missing: true

workflow:
  type: full  # or 'config-only'
  generate_tests: false

logging:
  level: INFO
  format: rich

limits:
  groups: []  # Empty means all groups
```

## 5. Acceptance Criteria

### Core Functionality

- **AC-001**: Given a valid AVD inventory path, When user runs `avd-cli generate all -i <path>`, Then configurations, documentation, and tests are generated successfully in `<path>/intended/`
- **AC-001.1**: Given a valid AVD inventory path and custom output, When user runs `avd-cli generate all -i <path> -o <output>`, Then configurations, documentation, and tests are generated successfully in `<output>/`
- **AC-001.2**: Given a valid AVD inventory path without output option, When user runs any generate subcommand, Then output defaults to `<inventory_path>/intended/` and informational message is displayed
- **AC-002**: Given the `configs` subcommand, When user runs `avd-cli generate configs -i <path>`, Then only configurations are generated in `<path>/intended/configs/`
- **AC-003**: Given the `docs` subcommand, When user runs `avd-cli generate docs -i <path>`, Then only documentation is generated in `<path>/intended/documentation/`
- **AC-004**: Given the `tests` subcommand, When user runs `avd-cli generate tests -i <path>`, Then only test files are generated in `<path>/intended/tests/`
- **AC-005**: Given the `--limit-to-groups` option with valid group names, When user runs any generate subcommand, Then only specified groups are processed
- **AC-006**: Given an invalid inventory path, When user runs any command, Then a clear error message is displayed with actionable guidance

### User Experience

- **AC-007**: Given any CLI command or command group, When user adds `--help` flag, Then comprehensive help text with examples is displayed
- **AC-008**: Given the `generate` command group, When user runs `avd-cli generate --help`, Then all available subcommands are listed with descriptions
- **AC-009**: Given a long-running operation, When processing takes >2 seconds, Then a progress indicator is displayed
- **AC-010**: Given a successful operation, When command completes, Then a summary table with statistics is displayed
- **AC-011**: Given an error condition, When error occurs, Then error message is formatted with Rich and includes suggested actions
- **AC-015**: Given any generate subcommand, When operation completes, Then output is displayed in consistent table format with category, count, and path
- **AC-016**: Given pyavd deprecation warnings, When user runs generate commands without flag, Then deprecation warnings are hidden
- **AC-017**: Given the `--show-deprecation-warnings` flag, When user runs generate commands, Then deprecation warnings from pyavd are displayed

### Environment Variables

- **AC-018**: Given any CLI option with environment variable support, When user runs command with `--help`, Then environment variable name is displayed in help text
- **AC-019**: Given an environment variable `AVD_CLI_INVENTORY_PATH=/path/to/inventory`, When user runs command without `-i` option, Then inventory path is loaded from environment variable
- **AC-020**: Given both environment variable and CLI argument, When user runs command, Then CLI argument takes precedence over environment variable
- **AC-021**: Given `AVD_CLI_LIMIT_TO_GROUPS=spine,leaf`, When user runs command, Then both groups are processed (comma-separated parsing)
- **AC-022**: Given `AVD_CLI_SHOW_DEPRECATION_WARNINGS=true`, When user runs command, Then deprecation warnings are shown
- **AC-023**: Given `AVD_CLI_SHOW_DEPRECATION_WARNINGS=1`, When user runs command, Then deprecation warnings are shown (numeric boolean support)
- **AC-024**: Given invalid environment variable value, When user runs command, Then clear validation error message is displayed

### Command Group Structure

- **AC-012**: Given the CLI architecture, When examining command structure, Then `generate` is a command group with subcommands
- **AC-013**: Given future extensibility needs, When adding new generation types, Then new subcommands can be added to `generate` group without breaking existing commands
- **AC-014**: Given the need for new use cases, When extending the CLI, Then new command groups can be added at the root level (e.g., `avd-cli deploy`, `avd-cli sync`)

### Code Quality

- **AC-010**: Given the complete codebase, When running pytest with coverage, Then coverage exceeds 80%
- **AC-011**: Given any Python file, When running pre-commit hooks, Then all linters pass without errors
- **AC-012**: Given any public function, When reviewing code, Then function has complete NumPy-style docstring
- **AC-013**: Given any module, When analyzing complexity, Then no function exceeds cyclomatic complexity of 10

## 6. Test Automation Strategy

### Test Levels

1. **Unit Tests** (tests/unit/)
   - Test individual functions and classes in isolation
   - Mock external dependencies (file system, py-avd calls)
   - Fast execution (<1s per test)
   - Cover all business logic branches

2. **Integration Tests** (tests/integration/)
   - Test component interactions
   - Use real file system with temporary directories
   - Test py-avd integration with mock data
   - Verify data flow between components

3. **End-to-End Tests** (tests/e2e/)
   - Test complete CLI commands
   - Use Click's CliRunner for command invocation
   - Validate output files and console output
   - Test real-world scenarios with sample inventories

### Frameworks and Tools

- **pytest**: Test framework with fixtures and parametrization
- **pytest-cov**: Coverage reporting and enforcement
- **pytest-mock**: Mocking and spying capabilities
- **Click.testing.CliRunner**: CLI command testing
- **unittest.mock**: Standard library mocking for complex scenarios

### Test Data Management

- **Fixtures**: Store sample AVD inventories in `tests/fixtures/`
- **Factory Functions**: Create test data programmatically
- **Cleanup**: Use pytest fixtures with teardown for resource cleanup
- **Isolation**: Each test has isolated temporary directories

### CI/CD Integration

- **GitHub Actions**: Run tests on every PR and push
- **Matrix Testing**: Test across Python 3.9, 3.10, 3.11, 3.13
- **Coverage Reporting**: Fail if coverage drops below 80%
- **Pre-commit**: Run linters and formatters automatically

### Coverage Requirements

- **Minimum Line Coverage**: 80%
- **Branch Coverage**: Track both true/false paths
- **Exclude**: Test files, migrations, generated code
- **Enforcement**: CI pipeline fails if threshold not met

### Performance Testing

- **Benchmark Tests**: Use pytest-benchmark for critical paths
- **Load Testing**: Test with large inventories (>100 devices)
- **Memory Profiling**: Monitor memory usage for large operations
- **Timeout**: Tests must complete within reasonable time limits

## 7. Rationale & Context

### Why Layered Architecture?

A layered architecture provides clear separation of concerns:

- **CLI Layer**: Handles user interaction and input validation
- **Logic Layer**: Contains business logic and AVD processing
- **Model Layer**: Defines data structures and validation rules

This separation enables:

- Independent testing of each layer
- Easy replacement of CLI framework if needed
- Reusability of business logic in other contexts
- Clear dependency flow (CLI → Logic → Models)

### Why Click over argparse?

Click provides several advantages:

- **Better UX**: Automatic help generation with beautiful formatting
- **Nested Commands**: Natural support for command groups
- **Type Conversion**: Automatic validation and type conversion
- **Environment Variables**: Built-in support with `envvar` parameter
- **Testing**: CliRunner for easy command testing
- **Extensibility**: Plugin architecture for future extensions

### Why Rich for Output?

Rich transforms CLI output from plain text to professional-grade UI:

- **Visual Hierarchy**: Tables, panels, trees for structured data
- **Progress Tracking**: Built-in progress bars and spinners
- **Color and Style**: Consistent theming across all output
- **Error Formatting**: Beautiful tracebacks with syntax highlighting
- **Professional Polish**: Makes CLI feel modern and user-friendly

### Why UV Package Manager?

UV offers modern Python package management:

- **Speed**: Significantly faster than pip/poetry
- **Reliability**: Deterministic dependency resolution
- **Simplicity**: Single tool for package management and script running
- **Standards**: Follows modern Python packaging standards
- **Integration**: Works seamlessly with pyproject.toml

### Why >80% Coverage Requirement?

High test coverage ensures:

- **Confidence**: Changes don't break existing functionality
- **Documentation**: Tests serve as usage examples
- **Design Quality**: Testable code is generally better designed
- **Regression Prevention**: Bugs are caught before production
- **Maintainability**: Future refactoring is safer

### Why Default Output to `<inventory_path>/intended`?

The default output directory follows AVD community best practices and conventions:

- **AVD Standard**: The `intended/` directory is the established convention in AVD repositories for storing generated artifacts
- **Co-location**: Keeping generated files within the inventory directory maintains project cohesion and simplifies path management
- **Git Integration**: Users can easily add `intended/` to `.gitignore` or commit it as needed, following standard AVD workflows
- **Discoverability**: Generated files are located in a predictable location relative to the source inventory
- **Simplicity**: Reduces the number of required CLI arguments for the most common use case (90%+ of users)
- **Convention over Configuration**: Follows the principle of sensible defaults while allowing customization when needed
- **Backwards Compatible**: Explicit `-o` / `--output-path` option still works for users who need custom output locations

**Migration Path**: Users can override the default with:

- CLI argument: `-o ./custom-output`
- Environment variable: `export AVD_CLI_OUTPUT_PATH=./custom-output`

### Why Command Groups for CLI Structure?

Using Click's command groups provides significant architectural benefits:

- **Extensibility**: Easy to add new subcommands without modifying existing code
- **Organization**: Related commands are logically grouped (e.g., all generation under `generate`)
- **Discoverability**: Users can explore available commands hierarchically
- **Future Growth**: New command groups can be added for different use cases:
  - `avd-cli deploy` - Deployment operations
  - `avd-cli sync` - Synchronization with devices
  - `avd-cli report` - Reporting and analytics
  - `avd-cli backup` - Backup and restore operations
- **Consistency**: Follows modern CLI patterns (like `git`, `kubectl`, `docker`)
- **Flexibility**: Each subcommand can have unique options while sharing common ones
- **Maintenance**: Changes to one subcommand don't affect others

### Why Two Workflow Modes?

The CLI supports two distinct workflow modes to accommodate different use cases:

**eos-design workflow** (default):

- **Purpose**: Complete automation from high-level design to CLI configurations
- **Rationale**:
  - Most AVD users start with fabric topology definitions
  - Abstracts complex EOS configurations into simple YAML structures
  - Automatically handles BGP, EVPN, MLAG, and underlay/overlay configurations
  - Reduces human error through standardized templates
- **Use Case**: Greenfield deployments, consistent fabric designs, infrastructure as code
- **Benefits**:
  - Single source of truth (fabric topology)
  - Automatic structured config generation
  - Consistent configurations across entire fabric

**cli-config workflow**:

- **Purpose**: Direct CLI generation when structured configs already exist
- **Rationale**:
  - Some users manually create structured configurations
  - Existing deployments may have pre-generated structured configs
  - Allows custom structured configs not generated by eos_design
  - Faster execution by skipping design phase
- **Use Case**: Brownfield deployments, custom configurations, partial AVD adoption, CI/CD optimization
- **Benefits**:
  - Faster execution (skips eos_design role)
  - Flexibility for custom structured configs
  - Lower memory footprint for large inventories
  - Suitable for iterative config updates

**Naming Convention Rationale**:

- `eos-design`: Clearly indicates the eos_design role is involved
- `cli-config`: Focuses on the final output (CLI configs) and the role used (eos_cli_config_gen)
- Avoids ambiguous terms like "full" or "config-only"
- Aligns with AVD role names for clarity

## 8. Dependencies & External Integrations

### External Systems

- **EXT-001**: Arista AVD Inventory - File-based Ansible inventory structure containing network device definitions and configurations
- **EXT-002**: py-avd Library - Python library providing AVD functionality for configuration generation and validation

### Third-Party Services

- **SVC-001**: None - CLI operates entirely offline with local file system

### Infrastructure Dependencies

- **INF-001**: File System - Read access to AVD inventory directory, write access to output directory
- **INF-002**: Python Runtime - Python 3.9+ interpreter with standard library

### Data Dependencies

- **DAT-001**: AVD Inventory Files - YAML format containing group_vars, host_vars, and inventory definitions
- **DAT-002**: AVD Schema - Implicit schema defined by py-avd library for inventory structure validation
- **DAT-003**: py-avd Schema Constants - Platform names and device types sourced from pyavd._eos_designs.schema module

### Technology Platform Dependencies

- **PLT-001**: Python 3.9-3.13 - Minimum version 3.9 for compatibility, tested up to 3.13
- **PLT-002**: UV Package Manager >= 0.5.1 - Required for dependency management and script execution
- **PLT-003**: Click Library - CLI framework for command structure and argument parsing
- **PLT-004**: Rich Library - Terminal formatting and output enhancement
- **PLT-005**: py-avd Library - Core AVD functionality (version to be determined by pyproject.toml)
- **PLT-006**: pytest Framework - Testing framework with fixtures and parametrization support

### Compliance Dependencies

- **COM-001**: PEP 8 Style Guide - Python code style compliance enforced through black and flake8
- **COM-002**: Type Checking - PEP 484 type hints enforced through mypy
- **COM-003**: Semantic Versioning - Version numbering following SemVer 2.0.0 specification

## 9. Examples & Edge Cases

### Default Output Directory Behavior

```bash
# Generate everything using default output path (./inventory/intended/)
avd-cli generate all -i ./inventory

# Expected output:
# → Loading inventory...
# ✓ Loaded 10 devices
# ℹ Using default output path: ./inventory/intended
# → Generating configurations...
# → Generating documentation...
# → Generating ANTA tests...
#
# ✓ Generated 3 output types
#
#                 Generated Files
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Category       ┃ Count ┃ Output Path                   ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Configurations │ 10    │ ./inventory/intended/configs  │
# │ Documentation  │ 10    │ ./inventory/intended/documentation │
# │ Tests          │ 2     │ ./inventory/intended/tests    │
# └────────────────┴───────┴───────────────────────────────┘

# Directory structure created:
# inventory/
# ├── inventory.yml
# ├── group_vars/
# ├── host_vars/
# └── intended/              # Auto-created default output directory
#     ├── configs/
#     │   ├── device1.cfg
#     │   └── device2.cfg
#     ├── documentation/
#     │   └── fabric-docs.md
#     └── tests/
#         ├── anta_catalog.yml
#         └── anta_inventory.yml
```

### Basic Configuration Generation with Custom Output

```bash
# Generate everything with explicit output path
avd-cli generate all -i ./inventory -o ./output

# Expected output:
# ╭─────────────────────────────────────────╮
# │   AVD Configuration Generation          │
# ╰─────────────────────────────────────────╯
#
# ✓ Validating inventory structure...
# ✓ Loading inventory data...
# ✓ Generating configurations...
# ✓ Generating documentation...
# ✓ Generating tests...
#
# ┏━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
# ┃ Category     ┃ Count ┃ Output Path    ┃
# ┡━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
# │ Devices      │ 24    │ output/configs │
# │ Configs      │ 24    │ output/configs │
# │ Docs         │ 24    │ output/docs    │
# │ Tests        │ 24    │ output/tests   │
# └──────────────┴───────┴────────────────┘
```

### Generate Specific Output Types

```bash
# Generate only configurations (uses default output)
avd-cli generate configs -i ./inventory

# Or with custom output path:
# avd-cli generate configs -i ./inventory -o ./output

# Expected output:
# → Loading inventory...
# ✓ Loaded 10 devices
# ℹ Using default output path: ./inventory/intended
# → Generating configurations...
#
# ✓ Generated 10 configuration files
#
#                   Generated Files
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Category       ┃ Count ┃ Output Path                   ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Configurations │ 10    │ ./inventory/intended/configs  │
# └────────────────┴───────┴───────────────────────────────┘

# Generate only documentation (uses default output)
avd-cli generate docs -i ./inventory

# Expected output:
# → Loading inventory...
# ✓ Loaded 10 devices
# ℹ Using default output path: ./inventory/intended
# → Generating documentation...
#
# ✓ Generated 10 documentation files
#
#                   Generated Files
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Category       ┃ Count ┃ Output Path                          ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Documentation  │ 10    │ ./inventory/intended/documentation   │
# └────────────────┴───────┴──────────────────────────────────────┘

# Generate only ANTA tests (uses default output)
avd-cli generate tests -i ./inventory

# Expected output:
# → Loading inventory...
# ✓ Loaded 10 devices
# ℹ Using default output path: ./inventory/intended
# → Generating ANTA tests...
#
# ✓ Generated 2 test files
#
#                   Generated Files
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Category       ┃ Count ┃ Output Path                  ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Tests          │ 2     │ ./inventory/intended/tests   │
# └────────────────┴───────┴──────────────────────────────┘
#
#                   Generated Files
# ┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Category       ┃ Count ┃ Output Path           ┃
# ┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Tests          │ 1     │ ./output/tests/tests  │
# └────────────────┴───────┴───────────────────────┘

# Expected behavior:
# - Only the specified output type is generated
# - Other output types are skipped
# - Faster execution time
# - Consistent table format across all commands
# - Clear feedback about what was generated
```

### Limited Group Processing

```bash
# Generate only for spine and leaf groups
avd-cli generate all -i ./inventory -o ./output -l spine -l leaf

# Generate configs only for specific groups
avd-cli generate configs -i ./inventory -o ./output -l spine

# Expected behavior:
# - Only devices in specified groups are processed
# - Other groups are skipped
# - Output contains only relevant files
```

### Workflow Modes

The `--workflow` option controls how AVD processes the inventory:

**eos-design workflow (default)**:

- **Purpose**: Complete AVD pipeline from fabric definitions to EOS CLI configurations
- **Process**:
  1. Reads fabric topology from group_vars (spine, l3leaf, l2leaf sections)
  2. Executes eos_design role to generate structured configurations
  3. Executes eos_cli_config_gen role to convert structured configs to CLI syntax
- **Use case**: Starting from high-level fabric design abstractions
- **Input**: AVD fabric definitions (topology, underlay, overlay settings)
- **Output**: Structured configs + CLI configs + documentation

**cli-config workflow**:

- **Purpose**: Direct CLI configuration generation from existing structured configurations
- **Process**:
  1. Reads existing structured configurations from Ansible inventory
  2. Executes eos_cli_config_gen role only
  3. Skips eos_design role entirely
- **Use case**: When structured configurations already exist (pre-generated or manually created)
- **Input**: Existing structured configurations in host_vars/group_vars
- **Output**: CLI configs + documentation

```bash
# eos-design workflow (complete pipeline)
avd-cli generate configs -i ./inventory -o ./output --workflow eos-design

# cli-config workflow (eos_cli_config_gen only)
avd-cli generate configs -i ./inventory -o ./output --workflow cli-config

# Show deprecation warnings
avd-cli generate configs -i ./inventory -o ./output --show-deprecation-warnings

# Expected behavior:
# - eos-design: Processes fabric topology -> structured configs -> CLI configs
# - cli-config: Processes existing structured configs -> CLI configs only
# - Deprecation warnings hidden by default, shown only with flag
```

### Environment Variable Usage

```bash
# Set environment variables
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_OUTPUT_PATH=./output
export AVD_CLI_WORKFLOW=eos-design

# Run command without explicit arguments
avd-cli generate configs

# Expected output:
# → Loading inventory...
# ✓ Loaded 10 devices from ./inventory
# → Generating configurations with workflow: eos-design
# ✓ Generated 10 configuration files
#
# Environment variables used:
#   AVD_CLI_INVENTORY_PATH: ./inventory
#   AVD_CLI_OUTPUT_PATH: ./output
#   AVD_CLI_WORKFLOW: eos-design

# Override environment variable with CLI argument
avd-cli generate configs -i ./other-inventory

# Expected output:
# → Loading inventory...
# ✓ Loaded 5 devices from ./other-inventory  (CLI argument overrides env var)

# Multiple groups via environment variable
export AVD_CLI_LIMIT_TO_GROUPS=spine,leaf,border
avd-cli generate configs

# Expected: Processes only spine, leaf, and border groups

# Boolean flags via environment variable
export AVD_CLI_SHOW_DEPRECATION_WARNINGS=true
avd-cli generate configs

# Expected: Shows deprecation warnings

# Numeric boolean
export AVD_CLI_SHOW_DEPRECATION_WARNINGS=1
avd-cli generate configs

# Expected: Shows deprecation warnings (1 == true)

# View help with environment variable info
avd-cli generate configs --help

# Expected output includes:
# Options:
#   -i, --inventory-path PATH  Path to AVD inventory directory  [env var:
#                              AVD_CLI_INVENTORY_PATH; required]
#   -o, --output-path PATH     Output directory for generated files  [env var:
#                              AVD_CLI_OUTPUT_PATH; required]
#   --workflow [full|config-only]
#                              Workflow type  [env var: AVD_CLI_WORKFLOW;
#                              default: full]
```

### Edge Cases

#### Empty Inventory

```python
# Given: Empty inventory directory
# When: User runs generate command
# Then: Clear error message displayed

"""
Error: No devices found in inventory
Path: /path/to/inventory

Suggestion: Ensure inventory contains:
  - group_vars/ directory
  - host_vars/ directory
  - At least one device definition
"""
```

#### Invalid YAML

```python
# Given: Inventory with malformed YAML
# When: User runs generate command
# Then: Specific file and error location shown

"""
Error: Invalid YAML syntax
File: inventory/group_vars/SPINES/spines.yml
Line: 42
Error: mapping values are not allowed here

Suggestion: Validate YAML syntax using:
  yamllint inventory/group_vars/SPINES/spines.yml
"""
```

#### Missing Required Fields

```python
# Given: Inventory missing required AVD fields
# When: User runs generate command
# Then: List of missing fields displayed

"""
Error: Required AVD fields missing

Device: spine1
Missing fields:
  - platform
  - mgmt_ip
  - type

Suggestion: Review AVD schema documentation:
  https://avd.arista.com/5.7/docs/
"""
```

#### Permission Denied

```python
# Given: No write permission to output directory
# When: User runs generate command
# Then: Permission error with suggestion

"""
Error: Cannot write to output directory
Path: /protected/output

Permission denied: /protected/output

Suggestion: Either:
  1. Use a different output path: -o ~/output
  2. Grant write permissions: chmod u+w /protected/output
  3. Run with appropriate privileges
"""
```

### Complex Workflow Example

```python
# Python API usage example for library integration
from pathlib import Path
from avd_cli.models.inventory import AvdInventory
from avd_cli.logics.processor import AvdProcessor
from avd_cli.exceptions import InvalidInventoryError

# Load and validate inventory
try:
    inventory = AvdInventory.load(Path("./inventory"))
    if not inventory.validate():
        raise InvalidInventoryError("Invalid inventory structure")

    # Create processor with specific workflow
    processor = AvdProcessor(
        workflow="full",
        generate_tests=True
    )

    # Process with group limits
    result = processor.generate(
        inventory_data=inventory.data,
        output_path=Path("./output"),
        limit_to_groups=["spine", "leaf"]
    )

    print(f"Generated {len(result.configs)} configurations")
    print(f"Generated {len(result.docs)} documentation files")
    print(f"Generated {len(result.tests)} test files")

except InvalidInventoryError as e:
    logger.error(f"Inventory validation failed: {e}")
except Exception as e:
    logger.error(f"Generation failed: {e}", exc_info=True)
```

## 10. Validation Criteria

### Code Quality Validation

- **VAL-001**: All Python files pass `black --check`
- **VAL-002**: All Python files pass `flake8` with zero errors
- **VAL-003**: All Python files pass `pylint` with score >= 9.0
- **VAL-004**: All Python files pass `mypy --strict`
- **VAL-005**: All functions have cyclomatic complexity <= 10

### Test Validation

- **VAL-006**: `pytest` runs with zero failures
- **VAL-007**: `pytest --cov` reports coverage >= 80%
- **VAL-008**: All acceptance criteria have corresponding tests
- **VAL-009**: All edge cases have test coverage
- **VAL-010**: CLI commands tested with CliRunner

### Documentation Validation

- **VAL-011**: All public functions have NumPy-style docstrings
- **VAL-012**: All CLI commands have `--help` text
- **VAL-013**: README.md includes installation and usage examples
- **VAL-014**: CHANGELOG.md follows Keep a Changelog format

### Integration Validation

- **VAL-015**: Successfully generates configs from sample AVD inventory
- **VAL-016**: Successfully generates ANTA tests when flag provided
- **VAL-017**: Successfully handles invalid inventory with clear errors
- **VAL-018**: Successfully processes large inventories (>100 devices)

### Environment Variable Validation

- **VAL-019**: All CLI options display corresponding environment variable in `--help` output
- **VAL-020**: Environment variables are correctly parsed and applied
- **VAL-021**: CLI arguments correctly override environment variables
- **VAL-022**: Comma-separated values in `AVD_CLI_LIMIT_TO_GROUPS` are correctly parsed
- **VAL-023**: Boolean environment variables accept `true`, `false`, `1`, `0` values
- **VAL-024**: Invalid environment variable values produce clear error messages

### Security Validation

- **VAL-025**: No hardcoded credentials or tokens in codebase
- **VAL-026**: All file paths sanitized before use
- **VAL-027**: Error messages don't expose internal implementation details
- **VAL-028**: Logging doesn't include sensitive information

## 11. Related Specifications / Further Reading

### Internal Specifications

- [Process: AVD Workflow Specification](./process-avd-workflow.md)
- [Data: AVD Inventory Schema](./data-avd-inventory-schema.md)
- [Design: CLI Interface Design](./design-cli-interface.md)
- [Infrastructure: Testing Strategy](./infrastructure-testing-strategy.md)

### External Documentation

- [Arista AVD Documentation](https://avd.arista.com/5.7/index.html)
- [py-avd Documentation](https://avd.arista.com/5.7/docs/pyavd/pyavd.html)
- [Click Documentation](https://click.palletsprojects.com/en/stable/)
- [Rich Documentation](https://github.com/Textualize/rich)
- [UV Documentation](https://docs.astral.sh/uv/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
