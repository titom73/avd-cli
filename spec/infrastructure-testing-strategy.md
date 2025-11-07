---
title: Testing Strategy and Infrastructure Specification
version: 1.0
date_created: 2025-11-06
last_updated: 2025-11-06
owner: AVD CLI Development Team
tags: [infrastructure, testing, pytest, coverage, quality]
---

# Introduction

This specification defines the comprehensive testing strategy, infrastructure requirements, and quality assurance practices for the AVD CLI project, ensuring >80% code coverage and maintainable test suites.

## 1. Purpose & Scope

### Purpose

Define testing practices to ensure:

- High code quality and reliability
- Comprehensive test coverage (>80%)
- Fast feedback loops for developers
- Confidence in refactoring and changes
- Clear testing patterns for all contributors

### Scope

- Unit, integration, and end-to-end testing strategies
- pytest configuration and best practices
- Test fixtures and data management
- Coverage requirements and measurement
- CI/CD integration for automated testing
- Performance and load testing approaches

### Audience

- Development team writing tests
- AI coding assistants generating test code
- Code reviewers validating test quality
- CI/CD engineers maintaining test infrastructure

### Assumptions

- pytest is the primary testing framework
- Tests run in Python 3.9-3.13 environments
- CI/CD runs on GitHub Actions
- UV package manager handles test dependencies

## 2. Definitions

- **Unit Test**: Test of individual function or class in isolation
- **Integration Test**: Test of multiple components working together
- **E2E Test**: End-to-end test of complete user workflows
- **Fixture**: Reusable test setup and teardown logic
- **Mock**: Simulated object replacing real dependencies
- **Coverage**: Percentage of code executed by tests
- **Parametrization**: Running same test with multiple input sets
- **Test Double**: Generic term for mocks, stubs, fakes, spies

## 3. Requirements, Constraints & Guidelines

### Coverage Requirements

- **COV-001**: Overall line coverage shall exceed 80%
- **COV-002**: Branch coverage shall be tracked and reported
- **COV-003**: New code shall not decrease overall coverage
- **COV-004**: Critical paths (CLI commands, data validation) shall have 100% coverage
- **COV-005**: Test files themselves excluded from coverage calculation
- **COV-006**: Coverage reports generated in both terminal and JSON formats

### Test Quality Requirements

- **QUA-001**: All tests shall have descriptive docstrings
- **QUA-002**: Test names shall clearly indicate what is being tested
- **QUA-003**: Each test shall test one specific behavior
- **QUA-004**: Tests shall be independent (no test interdependencies)
- **QUA-005**: Tests shall be deterministic (no random failures)
- **QUA-006**: All tests shall pass before merging to main branch

### Performance Requirements

- **PER-001**: Unit test suite shall complete in <30 seconds
- **PER-002**: Full test suite (including integration) shall complete in <5 minutes
- **PER-003**: Individual unit tests shall complete in <100ms
- **PER-004**: Integration tests may take up to 5 seconds each
- **PER-005**: Test setup/teardown shall be optimized for speed

### Maintainability Requirements

- **MAI-001**: Test code shall follow same quality standards as production code
- **MAI-002**: Duplicate test logic shall be extracted into fixtures or helpers
- **MAI-003**: Test data shall be managed centrally in fixtures directory
- **MAI-004**: Complex test setups shall use factory functions
- **MAI-005**: Tests shall use descriptive assertions with clear failure messages

### CI/CD Requirements

- **CIC-001**: Tests shall run automatically on all PRs
- **CIC-002**: Tests shall run on Python 3.9, 3.10, 3.11, 3.13
- **CIC-003**: Coverage shall be reported as PR comment
- **CIC-004**: Failed tests shall prevent merge
- **CIC-005**: Test results shall be visible in PR checks

### Constraints

- **CON-001**: Must use pytest framework (no unittest)
- **CON-002**: Must maintain fast test execution times
- **CON-003**: Must avoid external service dependencies in tests
- **CON-004**: Must use UV for running tests (`uv run pytest`)

### Guidelines

- **GUD-001**: Prefer simple assertions over complex custom matchers
- **GUD-002**: Use pytest fixtures over setup/teardown methods
- **GUD-003**: Use parametrize for testing multiple similar cases
- **GUD-004**: Mock external dependencies (file system, py-avd calls)
- **GUD-005**: Test error cases as thoroughly as success cases
- **GUD-006**: Use descriptive test failure messages
- **GUD-007**: Keep tests close to code they test

### Patterns

- **PAT-001**: AAA Pattern - Arrange, Act, Assert structure
- **PAT-002**: Given-When-Then for BDD-style tests
- **PAT-003**: Test Class per Production Class organization
- **PAT-004**: Factory Pattern for complex test data creation
- **PAT-005**: Builder Pattern for configurable test fixtures

## 4. Interfaces & Data Contracts

### pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--tb=short",
    "--cov=avd_cli",
    "--cov-report=term-missing",
    "--cov-report=json",
    "--cov-branch",
    "--cov-fail-under=80",
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, multiple components)",
    "e2e: End-to-end tests (slowest, full workflows)",
    "slow: Tests that take >1 second",
]
```

### Test Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── cli/
│   │   ├── test_commands.py
│   │   └── test_options.py
│   ├── models/
│   │   ├── test_inventory.py
│   │   └── test_device.py
│   └── logics/
│       ├── test_processor.py
│       └── test_validator.py
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_workflow.py
│   └── test_pyavd_integration.py
├── e2e/                           # End-to-end tests
│   ├── __init__.py
│   └── test_cli_commands.py
├── fixtures/                      # Test data and fixtures
│   ├── inventories/
│   │   ├── valid_minimal/
│   │   ├── valid_complete/
│   │   └── invalid_samples/
│   └── expected_outputs/
└── helpers/                       # Test helper functions
    ├── __init__.py
    ├── factories.py
    └── assertions.py
```

### Standard Test Patterns

```python
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from avd_cli.cli.commands import cli
from avd_cli.models.inventory import InventoryLoader
from avd_cli.exceptions import InvalidInventoryError


class TestInventoryLoader:
    """Test cases for InventoryLoader class.

    Follows AAA pattern: Arrange, Act, Assert.
    """

    @pytest.fixture
    def loader(self) -> InventoryLoader:
        """Create inventory loader instance for testing."""
        return InventoryLoader()

    @pytest.fixture
    def sample_inventory_path(self, tmp_path: Path) -> Path:
        """Create sample inventory structure.

        Returns
        -------
        Path
            Path to temporary inventory directory
        """
        inventory_dir = tmp_path / "inventory"
        inventory_dir.mkdir()

        # Create minimal valid structure
        group_vars = inventory_dir / "group_vars"
        group_vars.mkdir()

        fabric_file = group_vars / "FABRIC.yml"
        fabric_file.write_text("""
---
fabric_name: TEST_FABRIC
design:
  type: l3ls-evpn
""")

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
        assert inventory.root_path == sample_inventory_path
        assert len(inventory.fabrics) > 0

    def test_load_missing_directory_raises_error(
        self,
        loader: InventoryLoader,
        tmp_path: Path
    ) -> None:
        """Test loading non-existent directory raises clear error.

        Given: Non-existent inventory path
        When: load() is called
        Then: InvalidInventoryError with clear message
        """
        # Arrange
        nonexistent_path = tmp_path / "does_not_exist"

        # Act & Assert
        with pytest.raises(InvalidInventoryError) as exc_info:
            loader.load(nonexistent_path)

        assert "does not exist" in str(exc_info.value).lower()
        assert str(nonexistent_path) in str(exc_info.value)

    @pytest.mark.parametrize("invalid_structure,expected_error", [
        ("missing_group_vars", "group_vars directory not found"),
        ("empty_directory", "no inventory files found"),
        ("invalid_yaml", "YAML syntax error"),
    ])
    def test_load_invalid_structures(
        self,
        loader: InventoryLoader,
        tmp_path: Path,
        invalid_structure: str,
        expected_error: str
    ) -> None:
        """Test loading various invalid inventory structures.

        Parameters
        ----------
        invalid_structure : str
            Type of invalid structure to test
        expected_error : str
            Expected error message substring
        """
        # Arrange
        inventory_dir = tmp_path / invalid_structure
        inventory_dir.mkdir()

        if invalid_structure == "invalid_yaml":
            group_vars = inventory_dir / "group_vars"
            group_vars.mkdir()
            bad_yaml = group_vars / "bad.yml"
            bad_yaml.write_text("invalid: yaml: syntax:")

        # Act & Assert
        with pytest.raises(InvalidInventoryError) as exc_info:
            loader.load(inventory_dir)

        assert expected_error.lower() in str(exc_info.value).lower()


class TestCLICommands:
    """Test CLI command execution using Click's CliRunner."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI runner."""
        return CliRunner()

    def test_generate_command_with_valid_inventory(
        self,
        runner: CliRunner,
        sample_inventory_path: Path,
        tmp_path: Path
    ) -> None:
        """Test generate command with valid inputs.

        Given: Valid inventory and output paths
        When: generate command is executed
        Then: Command succeeds with zero exit code
        """
        # Arrange
        output_path = tmp_path / "output"

        # Act
        result = runner.invoke(cli, [
            'generate',
            '--inventory-path', str(sample_inventory_path),
            '--output-path', str(output_path)
        ])

        # Assert
        assert result.exit_code == 0
        assert "successfully" in result.output.lower()
        assert output_path.exists()

    def test_generate_command_help_text(self, runner: CliRunner) -> None:
        """Test generate command help is comprehensive.

        Given: No prior context
        When: generate --help is executed
        Then: Help text includes all options and examples
        """
        # Act
        result = runner.invoke(cli, ['generate', '--help'])

        # Assert
        assert result.exit_code == 0
        assert '--inventory-path' in result.output
        assert '--output-path' in result.output
        assert '--limit-to-groups' in result.output
        assert '--generate-tests' in result.output


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflow execution."""

    @pytest.fixture
    def mock_pyavd(self):
        """Mock py-avd library calls."""
        with patch('avd_cli.logics.processor.pyavd') as mock:
            mock.get_device_config.return_value = "! Device config"
            mock.get_device_doc.return_value = "# Device docs"
            yield mock

    def test_full_workflow_with_mocked_pyavd(
        self,
        sample_inventory_path: Path,
        tmp_path: Path,
        mock_pyavd: Mock
    ) -> None:
        """Test full workflow with mocked py-avd.

        Given: Valid inventory and mocked py-avd
        When: Full workflow executes
        Then: All components interact correctly
        """
        # Arrange
        from avd_cli.workflow import WorkflowExecutor

        executor = WorkflowExecutor()

        # Act
        result = executor.execute(
            inventory_path=sample_inventory_path,
            output_path=tmp_path / "output",
            mode="full",
            generate_tests=True,
            limit_to_groups=[],
            verbose=False
        )

        # Assert
        assert result.success
        assert mock_pyavd.get_device_config.called
        assert mock_pyavd.get_device_doc.called
```

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["avd_cli"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/site-packages/*",
]
branch = true

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstract",
]

[tool.coverage.json]
output = "coverage.json"
```

## 5. Acceptance Criteria

### Test Coverage

- **AC-001**: Given the test suite, When running pytest with coverage, Then line coverage exceeds 80%
- **AC-002**: Given new code added, When running coverage, Then coverage does not decrease
- **AC-003**: Given critical CLI commands, When measuring coverage, Then these paths have 100% coverage
- **AC-004**: Given coverage report, When reviewing, Then uncovered lines are justified or covered

### Test Execution

- **AC-005**: Given all unit tests, When running pytest, Then suite completes in <30 seconds
- **AC-006**: Given all tests, When running full suite, Then completes in <5 minutes
- **AC-007**: Given any test, When running independently, Then test passes without dependencies on other tests
- **AC-008**: Given test suite, When running multiple times, Then results are identical (deterministic)

### Test Quality

- **AC-009**: Given any test, When reading code, Then test purpose is clear from name and docstring
- **AC-010**: Given any test failure, When reading output, Then failure message clearly indicates problem
- **AC-011**: Given test code, When reviewing, Then tests follow AAA pattern consistently
- **AC-012**: Given parametrized tests, When reviewing, Then parameter names are descriptive

### CI/CD Integration

- **AC-013**: Given PR submitted, When CI runs, Then tests execute on all supported Python versions
- **AC-014**: Given test failure, When viewing PR, Then failure is visible in PR checks
- **AC-015**: Given coverage results, When PR completes, Then coverage comment is added to PR
- **AC-016**: Given coverage drop, When detected, Then PR check fails

## 6. Test Automation Strategy

### Test Levels

#### Unit Tests (tests/unit/)

**Purpose**: Test individual functions/classes in isolation

**Characteristics**:

- Fast (<100ms per test)
- No file I/O or network calls
- Mock external dependencies
- Test single behavior per test

**What to Test**:

- Function input/output correctness
- Error handling and edge cases
- Data validation logic
- Business rule enforcement

**Example**:

```python
@pytest.mark.unit
def test_device_hostname_validation():
    """Test device hostname validation rules."""
    # Valid hostnames
    assert validate_hostname("spine1") is True
    assert validate_hostname("leaf-01") is True

    # Invalid hostnames
    assert validate_hostname("spine#1") is False
    assert validate_hostname("") is False
```

#### Integration Tests (tests/integration/)

**Purpose**: Test multiple components working together

**Characteristics**:

- Slower (up to 5s per test)
- May use real file system (temporary directories)
- Mock only external services
- Test component interactions

**What to Test**:

- Data flow between components
- File reading/writing operations
- py-avd integration (with mocks)
- Workflow stage transitions

**Example**:

```python
@pytest.mark.integration
def test_inventory_to_config_pipeline(tmp_path):
    """Test complete pipeline from inventory to config."""
    # Setup real inventory files
    inventory = create_test_inventory(tmp_path)

    # Load and process (real file I/O)
    loader = InventoryLoader()
    data = loader.load(inventory)

    # Generate configs (mocked py-avd)
    with patch('pyavd.get_device_config') as mock:
        mock.return_value = "! Config"
        processor = ConfigProcessor()
        result = processor.generate(data, tmp_path / "output")

    # Verify output files created
    assert (tmp_path / "output" / "configs").exists()
```

#### End-to-End Tests (tests/e2e/)

**Purpose**: Test complete user workflows

**Characteristics**:

- Slowest (may take several seconds)
- Test through CLI interface
- Use CliRunner from Click
- Minimal mocking

**What to Test**:

- Complete CLI commands
- Real-world user scenarios
- Error message display
- Output file generation

**Example**:

```python
@pytest.mark.e2e
def test_complete_generate_workflow(runner, sample_inventory):
    """Test full generate command workflow."""
    result = runner.invoke(cli, [
        'generate',
        '-i', str(sample_inventory),
        '-o', './output',
        '--generate-tests'
    ])

    assert result.exit_code == 0
    assert Path('./output/configs').exists()
    assert Path('./output/tests').exists()
```

### Fixture Strategy

#### Scope Optimization

```python
# Session scope - created once per test session
@pytest.fixture(scope="session")
def shared_test_data():
    """Expensive setup done once."""
    return load_large_dataset()

# Module scope - created once per test module
@pytest.fixture(scope="module")
def database_connection():
    """Setup DB connection per module."""
    conn = create_connection()
    yield conn
    conn.close()

# Function scope (default) - created per test
@pytest.fixture
def temp_inventory(tmp_path):
    """Fresh inventory for each test."""
    return create_inventory(tmp_path)
```

#### Fixture Composition

```python
@pytest.fixture
def inventory_path(tmp_path):
    """Create inventory directory structure."""
    inv_path = tmp_path / "inventory"
    inv_path.mkdir()
    return inv_path

@pytest.fixture
def group_vars(inventory_path):
    """Create group_vars in inventory."""
    gv = inventory_path / "group_vars"
    gv.mkdir()
    return gv

@pytest.fixture
def complete_inventory(inventory_path, group_vars):
    """Compose complete inventory from parts."""
    # Use both dependencies
    create_fabric_file(group_vars / "FABRIC.yml")
    return inventory_path
```

### Mocking Strategy

```python
# Mock external dependencies
from unittest.mock import Mock, patch, MagicMock

# Mock function return value
@patch('avd_cli.logics.processor.get_config')
def test_with_mocked_function(mock_get_config):
    mock_get_config.return_value = "config content"
    # Test code

# Mock object method
def test_with_mocked_object():
    mock_pyavd = Mock()
    mock_pyavd.get_device_config.return_value = "! Config"
    # Test code

# Mock file system operations
@patch('pathlib.Path.exists')
def test_with_mocked_fs(mock_exists):
    mock_exists.return_value = True
    # Test code
```

## 7. Rationale & Context

### Why >80% Coverage?

80% coverage strikes balance between:

- **Confidence**: Most code paths are tested
- **Pragmatism**: 100% is often impractical
- **Industry Standard**: Widely accepted threshold
- **Maintainability**: Higher coverage aids refactoring

### Why pytest over unittest?

pytest provides superior DX:

- **Simpler Syntax**: Plain `assert` vs `self.assertEqual`
- **Better Fixtures**: More flexible than setUp/tearDown
- **Parametrization**: Easy multiple-input testing
- **Plugin Ecosystem**: Rich extension capabilities
- **Better Output**: Clear, readable failure messages

### Why AAA Pattern?

Arrange-Act-Assert structure provides:

- **Clarity**: Each test section has clear purpose
- **Readability**: Easy to understand test flow
- **Maintainability**: Consistent structure across tests
- **Debugging**: Easy to identify which phase failed

## 8. Dependencies & External Integrations

### Technology Platform Dependencies

- **PLT-001**: pytest >= 7.0 - Test framework
- **PLT-002**: pytest-cov - Coverage measurement
- **PLT-003**: pytest-mock - Enhanced mocking capabilities
- **PLT-004**: pytest-xdist (optional) - Parallel test execution
- **PLT-005**: Click testing utilities - CLI testing support

### Infrastructure Dependencies

- **INF-001**: GitHub Actions - CI/CD test execution
- **INF-002**: UV Package Manager - Test dependency management and execution

### Data Dependencies

- **DAT-001**: Test Fixtures - Sample inventories and expected outputs stored in tests/fixtures/

## 9. Examples & Edge Cases

See code examples throughout Section 4 and Section 6.

## 10. Validation Criteria

### Pre-Merge Validation

- **VAL-001**: All tests pass on all supported Python versions
- **VAL-002**: Coverage meets or exceeds 80% threshold
- **VAL-003**: No test warnings or deprecation notices
- **VAL-004**: Test execution time within limits

### Code Review Validation

- **VAL-005**: New features include corresponding tests
- **VAL-006**: Tests follow established patterns
- **VAL-007**: Test names are descriptive
- **VAL-008**: Complex logic has parametrized tests

## 11. Related Specifications / Further Reading

### Internal Specifications

- [Tool: AVD CLI Architecture](./tool-avd-cli-architecture.md)
- [Process: AVD Workflow](./process-avd-workflow.md)
- [Data: AVD Inventory Schema](./data-avd-inventory-schema.md)

### External Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Click Testing](https://click.palletsprojects.com/en/stable/testing/)
