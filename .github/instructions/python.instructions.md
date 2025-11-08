---
applyTo: '**/*.py'
description: 'Python coding standards, best practices, and project-specific conventions for avd-cli.'
---

# Python Coding Standards for avd-cli

## Your Mission

As GitHub Copilot working on Python code in **avd-cli**, you must follow strict Python coding standards, project conventions, and best practices. This ensures code quality, maintainability, and consistency across the codebase.

## Development Environment

### UV Package Manager

**This project uses UV as the primary package and project management tool.** UV is a fast, modern Python package manager that provides:

- Fast dependency resolution and installation
- Integrated project management (pyproject.toml)
- Built-in virtual environment management
- Python version management
- Lock file support for reproducible builds

**Key UV Commands:**

```bash
# Run Python scripts with UV
uv run python script.py

# Execute commands in the UV environment
uv run pytest
uv run mypy avd_cli
uv run flake8 avd_cli

# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Run a tool without installing it globally
uvx ruff check avd_cli
```

**In Code and Documentation:**

- Always reference UV commands in examples and documentation
- When suggesting package installation, use `uv add` instead of `pip install`
- When running tests or scripts, use `uv run` prefix
- Assume UV is available in the development environment

**Makefile Integration:**

The project's Makefile uses UV for all operations:

```makefile
# Examples from the project
ci-test:
	uv run pytest tests/

ci-lint:
	uv run flake8 avd_cli
	uv run pylint avd_cli

ci-type:
	uv run mypy --strict avd_cli
```

## Python Version Support

- **Minimum**: Python 3.9
- **Tested**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Use modern Python features**: Type hints, f-strings, pathlib, dataclasses, async/await where appropriate

## Requirements

Code must be valid and pass without errors or warnings through the following tools:

- black
- mypy
- flake8
- pylint

Configuration to follow for these tools is located in the project root with pre-commit configuration file: `.pre-commit-config.yaml`.

## Code Style

### Docstring format

Code comments must follow docstrings based on the NumPy style.

Example:

```python
# -*- coding: utf-8 -*-
"""Example NumPy style docstrings.

This module demonstrates documentation as specified by the `NumPy
Documentation HOWTO`_. Docstrings may extend over multiple lines. Sections
are created with a section header followed by an underline of equal length.

Example
-------
Examples can be given using either the ``Example`` or ``Examples``
sections. Sections support any reStructuredText formatting, including
literal blocks::

    $ python example_numpy.py


Section breaks are created with two blank lines. Section breaks are also
implicitly created anytime a new section starts. Section bodies *may* be
indented:

Notes
-----
    This is an example of an indented section. It's like any other section,
    but the body is indented to help it stand out from surrounding text.

If a section is indented, then a section break is created by
resuming unindented text.

Attributes
----------
module_level_variable1 : int
    Module level variables may be documented in either the ``Attributes``
    section of the module docstring, or in an inline docstring immediately
    following the variable.

    Either form is acceptable, but the two should not be mixed. Choose
    one convention to document module level variables and be consistent
    with it.


.. _NumPy Documentation HOWTO:
   https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

"""

def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.

    `PEP 484`_ type annotations are supported. If attribute, parameter, and
    return types are annotated according to `PEP 484`_, they do not need to be
    included in the docstring:

    Parameters
    ----------
    param1 : int
        The first parameter.
    param2 : str
        The second parameter.

    Returns
    -------
    bool
        True if successful, False otherwise.

    .. _PEP 484:
        https://www.python.org/dev/peps/pep-0484/

    """
```

Reference: <https://numpy.org/doc/1.19/docs/howto_document.html>

### PEP 8 Compliance

Always follow PEP 8 with these project-specific conventions:

```python
# ✅ Good: PEP 8 compliant
def download_eos_image(
    version: str,
    image_format: str,
    output_dir: Path,
    token: str,
) -> Path:
    """Download an EOS image from Arista server."""
    pass

# ❌ Bad: Non-compliant
def downloadEosImage(version,imageFormat,outputDir,token):  # camelCase, no spaces
    pass
```

### Line Length

- **Maximum**: 120 characters (configured in project)
- **Docstrings**: 100 characters for better readability
- **Comments**: 72 characters

### Import Organization

Always organize imports in this order:

```python
#!/usr/bin/env python
# coding: utf-8 -*-

"""Module docstring."""

# Standard library imports (alphabetically sorted within groups)
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Third-party imports (alphabetically sorted)
import click
from rich.console import Console
from rich.table import Table

# Local application imports (alphabetically sorted)
from avd_cli.exceptions import ValidationError, LoaderError
from avd_cli.logics.generator import ConfigurationGenerator
from avd_cli.models.inventory import DeviceDefinition
```

### Lazy Imports for CLI Performance

For CLI applications, use **lazy imports** (imports inside functions) for heavy dependencies to improve startup time and user experience:

```python
# ✅ Good: Lazy imports in CLI commands
@click.command()
def generate_configs(inventory_path: Path, output_path: Path) -> None:
    """Generate configurations from inventory.

    Heavy imports are loaded only when the command is actually executed,
    not when the user runs --help or other commands.
    """
    # Import heavy dependencies only when needed
    from avd_cli.logics.generator import ConfigurationGenerator
    from avd_cli.logics.loader import InventoryLoader

    # Import pyavd-dependent modules only when command runs
    import pyavd

    # Command implementation...
    loader = InventoryLoader()
    inventory = loader.load(inventory_path)

# ❌ Bad: Top-level imports slow down ALL CLI operations
from avd_cli.logics.generator import ConfigurationGenerator
from avd_cli.logics.loader import InventoryLoader
import pyavd  # Loads heavy dependency even for --help

@click.command()
def generate_configs(inventory_path: Path, output_path: Path) -> None:
    """Generate configurations from inventory."""
    # Now --help is slow because pyavd is already loaded
    pass
```

**When to use lazy imports:**

- ✅ CLI commands that load heavy libraries (pyavd, pandas, etc.)
- ✅ Optional dependencies that might not be installed
- ✅ Modules with expensive initialization
- ✅ Commands that aren't always used (avoids loading for `--help`, `--version`)

**When NOT to use lazy imports:**

- ❌ Core library modules (use top-level imports)
- ❌ Type checking imports (use `TYPE_CHECKING` guard instead)
- ❌ Constants, exceptions, and lightweight utilities
- ❌ Standard library imports (already fast)

**Rationale:**

- **UX**: `avd-cli --help` should be instant (<100ms)
- **Performance**: Don't load pyavd/heavy libs unless actually needed
- **Dependency isolation**: Allows showing help even if optional deps missing
- **Convention**: Approved by pylint configuration (C0415 disabled)

## Type Hints

### Mandatory Type Hints

Always provide type hints for:

- Function parameters
- Function return types
- Class attributes
- Module-level variables

```python
# ✅ Good: Complete type hints
from typing import Optional, List, Dict, Any
from pathlib import Path

def process_versions(
    versions: List[EosVersion],
    filter_branch: Optional[str] = None,
    output_format: str = "json",
) -> Dict[str, Any]:
    """Process and format version information.

    Parameters
    ----------
    versions : List[EosVersion]
        List of EOS versions to process
    filter_branch : Optional[str], optional
        Branch to filter by, by default None
    output_format : str, optional
        Output format (json, text, fancy), by default "json"

    Returns
    -------
    Dict[str, Any]
        Processed version data
    """
    results: Dict[str, Any] = {}
    filtered: List[EosVersion] = [
        v for v in versions
        if filter_branch is None or v.branch == filter_branch
    ]
    return results

# ❌ Bad: Missing type hints
def process_versions(versions, filter_branch=None):
    results = {}
    return results
```

### Use Modern Type Hints

```python
# ✅ Good: Modern Python 3.9+ type hints
from typing import Optional

def get_version(version_str: str) -> Optional[EosVersion]:
    """Get version or None if not found."""
    pass

# For Python 3.10+ you can use the | operator
def get_version(version_str: str) -> EosVersion | None:
    """Get version or None if not found."""
    pass

# ✅ Good: Generic types
from typing import Dict, List, Tuple

def get_mapping() -> Dict[str, List[str]]:
    """Return mapping of formats to extensions."""
    return {"64": [".swi"], "cEOS": [".tar", ".tar.gz"]}

# ❌ Bad: Using dict, list without type parameters
def get_mapping() -> dict:
    return {"64": [".swi"]}
```

## Documentation Standards

### Module Docstrings

Every module must have a comprehensive docstring:

```python
#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=line-too-long

"""
Module for managing EOS image downloads.

This module provides functionality to download, validate, and manage
Arista EOS software images from the official Arista repository.

Classes
-------
EosDownloader
    Main class for downloading EOS images
SoftManager
    Manages software download operations

Functions
---------
download_eos_image
    Download a specific EOS image version
validate_checksum
    Validate downloaded file integrity
generate_filename
    Generate standard filename for EOS images

Examples
--------
Basic usage:

>>> from avd_cli.logics.loader import InventoryLoader
>>> loader = InventoryLoader()
>>> inventory = loader.load("inventory.yml")

With configuration:

>>> from avd_cli.logics.generator import ConfigurationGenerator
>>> generator = ConfigurationGenerator(workflow="eos-design")
>>> generator.generate_structured_configs(inventory)

Notes
-----
Requires valid AVD inventory structure.

See Also
--------
avd_cli.logics.generator : Configuration generation logic
avd_cli.models.inventory : Inventory data models
"""
```

### Function/Method Docstrings

Use NumPy style docstrings:

```python
def generate_device_config(
    device: DeviceDefinition,
    workflow: str,
    output_dir: Path,
    validate: bool = True,
) -> Path:
    """Generate configuration for a device using AVD workflow.

    This function generates structured configurations for the specified
    device using the AVD workflow, saves it to the output directory, and
    optionally validates the configuration against the schema.

    Parameters
    ----------
    device : DeviceDefinition
        Device definition from AVD inventory
    workflow : str
        AVD workflow to use. One of: "eos-design", "cli-config"
    output_dir : Path
        Directory where the configuration will be saved
    validate : bool, optional
        Whether to validate configuration against schema, by default True

    Returns
    -------
    Path
        Path to the generated configuration file

    Raises
    ------
    ValidationError
        If the device definition or generated config fails validation
    LoaderError
        If required inventory data is missing or invalid
    ValueError
        If the workflow is not supported
    FileNotFoundError
        If the output directory does not exist and cannot be created

    Examples
    --------
    Generate configuration for a device:

    >>> config_path = generate_device_config(
    ...     device=device,
    ...     workflow="eos-design",
    ...     output_dir=Path("/configs"),
    ... )
    >>> print(f"Configuration saved to: {config_path}")
    Configuration saved to: /configs/leaf1.cfg

    Generate without validation:

    >>> config_path = generate_device_config(
    ...     device=device,
    ...     workflow="cli-config",
    ...     output_dir=Path("/tmp"),
    ...     validate=False
    ... )

    Notes
    -----
    - Requires a valid AVD inventory structure
    - Configuration generation may take time for complex topologies
    - The function will create the output directory if it doesn't exist

    See Also
    --------
    validate_configuration : Verify configuration against schema
    ConfigurationGenerator : Main generator class
    """
    # Implementation
    pass
```

### Class Docstrings

```python
class ConfigurationGenerator:
    """Generate device configurations from AVD inventory.

    This class provides a high-level interface for generating device
    configurations using AVD workflows. It handles inventory loading,
    validation, and configuration generation.

    Parameters
    ----------
    workflow : str, optional
        AVD workflow to use, by default "eos-design"
    validate : bool, optional
        Whether to validate configurations, by default True

    Attributes
    ----------
    workflow : str
        The active workflow name
    inventory : InventoryModel
        Loaded AVD inventory
    validate : bool
        Validation flag

    Examples
    --------
    Basic usage:

    >>> generator = ConfigurationGenerator(workflow="eos-design")
    >>> generator.load_inventory("inventory.yml")
    >>> configs = generator.generate_structured_configs()

    With custom workflow:

    >>> generator = ConfigurationGenerator(
    ...     workflow="cli-config",
    ...     validate=True
    ... )

    Notes
    -----
    Always validate inventory structure before generating configurations.

    See Also
    --------
    InventoryLoader : Inventory loading and parsing
    DocumentationGenerator : Generate documentation from inventory
    """

    def __init__(
        self,
        token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the EOS downloader."""
        self.token = token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
```

## Error Handling

### Use Project-Specific Exceptions

```python
# ✅ Good: Specific exception handling
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
    except ValidationError as e:
        raise LoaderError(
            f"Inventory validation failed: {e}"
        ) from e

# ❌ Bad: Generic exception handling
def load_inventory_bad(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:  # Too broad
        print(f"Error: {e}")  # Poor error handling
        return None  # Silent failure
```

### Exception Chaining

Always use `from e` to preserve exception context:

```python
# ✅ Good: Exception chaining
try:
    data = parse_xml(content)
except ET.ParseError as e:
    raise ValueError(f"Invalid XML format: {e}") from e

# ❌ Bad: Lost exception context
try:
    data = parse_xml(content)
except ET.ParseError as e:
    raise ValueError(f"Invalid XML format")  # Lost original error
```

## Logging

### Use Structured Logging

```python
# ✅ Good: Structured logging with context
import logging

logger = logging.getLogger(__name__)

def download_file(url: str, output_path: Path) -> None:
    """Download file with proper logging."""
    logger.info(
        "Starting file download",
        extra={
            "url": url,
            "output_path": str(output_path),
            "operation": "download_start"
        }
    )

    try:
        # Generation logic
        result = generation_logic(inventory, output_path)

        logger.info(
            "Configuration generation completed",
            extra={
                "inventory_path": str(inventory_path),
                "output_path": str(output_path),
                "device_count": result.device_count,
                "operation": "generation_complete"
            }
        )

    except LoaderError as e:
        logger.error(
            "Configuration generation failed",
            extra={
                "inventory_path": str(inventory_path),
                "error": str(e),
                "operation": "generation_failed"
            },
            exc_info=True
        )
        raise

# ❌ Bad: Print statements and poor logging
def generate_configs_bad(inventory_path, output_path):
    print(f"Generating from {inventory_path}")  # Should use logging
    try:
        generation_logic(inventory_path, output_path)
        print("Done")  # No context
    except Exception as e:
        print(f"Error: {e}")  # No structured data
```

### Log Levels

Use appropriate log levels:

```python
# DEBUG: Detailed diagnostic information
logger.debug("Inventory data: %s", inventory_data[:100])

# INFO: Normal operations and confirmations
logger.info("Loaded 10 devices from inventory")

# WARNING: Something unexpected but handled
logger.warning("Device missing optional group_vars file")

# ERROR: Error that prevents operation
logger.error("Failed to generate configuration", exc_info=True)

# CRITICAL: System-level failure
logger.critical("Unable to load required AVD inventory")
```

## Path Handling

### Always Use pathlib

```python
from pathlib import Path

# ✅ Good: Using pathlib
def save_file(content: bytes, output_dir: Path, filename: str) -> Path:
    """Save file using pathlib."""
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    # Build path safely
    output_path = output_dir / safe_filename

    # Write file
    output_path.write_bytes(content)

    return output_path

# ❌ Bad: String concatenation
def save_file_bad(content, output_dir, filename):
    # Path traversal risk
    output_path = output_dir + "/" + filename

    # No directory creation
    with open(output_path, 'wb') as f:
        f.write(content)

    return output_path
```

### File Operations

```python
# ✅ Good: Safe file operations with context managers
from pathlib import Path

def read_config(config_path: Path) -> Dict[str, Any]:
    """Read configuration file safely."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if not config_path.is_file():
        raise ValueError(f"Path is not a file: {config_path}")

    try:
        with config_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config: {e}") from e

# ✅ Good: Writing files safely
def write_data(data: Dict[str, Any], output_path: Path) -> None:
    """Write data to file safely."""
    # Create parent directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically (temp file + rename)
    temp_path = output_path.with_suffix('.tmp')
    try:
        with temp_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        temp_path.replace(output_path)
    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise
```

## Resource Management

### Always Use Context Managers

```python
# ✅ Good: Context managers for resource cleanup
def download_with_session(urls: List[str]) -> List[bytes]:
    """Download multiple files using session."""
    results = []

    with requests.Session() as session:
        session.headers.update(DEFAULT_REQUEST_HEADERS)

        for url in urls:
            response = session.get(url)
            response.raise_for_status()
            results.append(response.content)

    return results

# ✅ Good: File handling
def process_large_file(file_path: Path) -> int:
    """Process large file line by line."""
    line_count = 0

    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            process_line(line)
            line_count += 1

    return line_count

# ❌ Bad: Manual resource management
def download_with_session_bad(urls):
    session = requests.Session()
    results = []
    for url in urls:
        response = session.get(url)
        results.append(response.content)
    session.close()  # Might not be called if exception occurs
    return results
```

## Performance Best Practices

### Use Lazy Evaluation

```python
from typing import Generator

# ✅ Good: Generator for memory efficiency
def iter_versions(
    xml_root: ET.Element
) -> Generator[EosVersion, None, None]:
    """Iterate over versions without loading all into memory."""
    for node in xml_root.findall('.//dir[@label]'):
        if label := node.get("label"):
            try:
                version = EosVersion.from_str(label)
                yield version
            except ValueError:
                # Skip invalid versions
                continue

# ❌ Bad: Load everything into memory
def get_all_versions(xml_root):
    versions = []
    for node in xml_root.findall('.//dir[@label]'):
        label = node.get("label")
        if label:
            try:
                versions.append(EosVersion.from_str(label))
            except ValueError:
                pass
    return versions  # High memory usage for large datasets
```

### Use Caching Appropriately

```python
from functools import lru_cache

# ✅ Good: Cache expensive operations
@lru_cache(maxsize=128)
def get_software_catalog(token: str) -> ET.Element:
    """Get and cache software catalog XML.

    Cached per token to avoid redundant API calls.
    """
    response = requests.get(
        CATALOG_URL,
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return ET.fromstring(response.content)

# ✅ Good: Cache validation results
@lru_cache(maxsize=1024)
def validate_version_format(version: str) -> bool:
    """Validate version format (cached for performance)."""
    return bool(EosVersion.regex_version.match(version))
```

### Concurrent Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable

# ✅ Good: Parallel downloads
def download_multiple_files(
    urls: List[str],
    dest_dir: Path,
    max_workers: int = 4
) -> List[Path]:
    """Download multiple files concurrently.

    Parameters
    ----------
    urls : List[str]
        URLs to download
    dest_dir : Path
        Destination directory
    max_workers : int, optional
        Maximum number of concurrent downloads, by default 4

    Returns
    -------
    List[Path]
        Paths to downloaded files
    """
    results: List[Path] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_url = {
            executor.submit(download_file, url, dest_dir): url
            for url in urls
        }

        # Process completed downloads
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Downloaded: {url}")
            except Exception as e:
                logger.error(f"Failed to download {url}: {e}")

    return results
```

## Testing Guidelines

### Use Pytest

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# ✅ Good: Well-structured test class
class TestEosDownloader:
    """Test suite for EOS downloader functionality."""

    @pytest.fixture
    def mock_token(self) -> str:
        """Provide a mock API token for testing."""
        return "test-token-abc123xyz"

    @pytest.fixture
    def temp_output_dir(self, tmp_path: Path) -> Path:
        """Provide a temporary output directory."""
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def mock_arista_response(self) -> str:
        """Provide mock XML response from Arista API."""
        return """
        <folder>
            <dir label="Active Releases">
                <dir label="4.29.3M">
                    <file>EOS-4.29.3M.swi</file>
                </dir>
            </dir>
        </folder>
        """

    def test_version_parsing_valid(self) -> None:
        """Test parsing of valid EOS version strings."""
        version = EosVersion.from_str("4.29.3M")

        assert version.major == 4
        assert version.minor == 29
        assert version.patch == 3
        assert version.rtype == "M"
        assert version.branch == "4.29"

    def test_version_parsing_invalid(self) -> None:
        """Test that invalid version strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid version format"):
            EosVersion.from_str("invalid-version")

    @pytest.mark.parametrize(
        "version_str,expected_major,expected_minor,expected_patch,expected_rtype",
        [
            ("4.29.3M", 4, 29, 3, "M"),
            ("4.30.1F", 4, 30, 1, "F"),
            ("4.28.10M", 4, 28, 10, "M"),
            ("4.31.0F", 4, 31, 0, "F"),
        ]
    )
    def test_version_parsing_parametrized(
        self,
        version_str: str,
        expected_major: int,
        expected_minor: int,
        expected_patch: int,
        expected_rtype: str
    ) -> None:
        """Test version parsing with multiple inputs."""
        version = EosVersion.from_str(version_str)

        assert version.major == expected_major
        assert version.minor == expected_minor
        assert version.patch == expected_patch
        assert version.rtype == expected_rtype

    @patch('requests.get')
    def test_download_success(
        self,
        mock_get: Mock,
        mock_token: str,
        temp_output_dir: Path
    ) -> None:
        """Test successful file download."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake EOS image content"
        mock_response.headers = {"Content-Length": "23"}
        mock_get.return_value = mock_response

        # Execute
        downloader = SoftManager()
        result = downloader.download_file(
            url="https://example.com/EOS-4.29.3M.swi",
            output_dir=temp_output_dir,
            filename="EOS-4.29.3M.swi"
        )

        # Assert
        assert result.exists()
        assert result.name == "EOS-4.29.3M.swi"
        assert result.read_bytes() == b"fake EOS image content"
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_download_with_expired_token(
        self,
        mock_get: Mock,
        mock_token: str,
        temp_output_dir: Path
    ) -> None:
        """Test download fails gracefully with expired token."""
        # Setup mock to return 401
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_get.return_value = mock_response

        # Execute and assert
        downloader = SoftManager()
        with pytest.raises(TokenExpiredError):
            downloader.download_file(
                url="https://example.com/file.swi",
                output_dir=temp_output_dir,
                filename="test.swi"
            )
```

## Code Quality Tools

### Configuration

The project uses these tools (configured in `pyproject.toml`):

- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pylint**: Additional linting
- **isort**: Import sorting

### Run Before Committing

**All commands use UV to run in the project environment:**

```bash
# Format code
uv run black avd_cli/

# Sort imports
uv run isort avd_cli/

# Type check
uv run mypy avd_cli/

# Lint
uv run flake8 avd_cli/
uv run pylint avd_cli/

# Run all tests
uv run pytest tests/

# Or use make commands (which internally use UV)
make ci-test    # Run tests with coverage
make ci-lint    # Run linters
make ci-type    # Run type checking
```

## Common Anti-Patterns to Avoid

1. ❌ **Mutable default arguments**

```python
# ❌ Bad
def add_item(item, items=[]):  # Shared between calls!
    items.append(item)
    return items

# ✅ Good
def add_item(item: str, items: Optional[List[str]] = None) -> List[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

2. ❌ **Catching Exception without context**

```python
# ❌ Bad
try:
    risky_operation()
except Exception:
    pass  # Silent failure

# ✅ Good
try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

3. ❌ **Not using context managers**

```python
# ❌ Bad
f = open("file.txt")
data = f.read()
f.close()

# ✅ Good
with open("file.txt") as f:
    data = f.read()
```

4. ❌ **String formatting with %**

```python
# ❌ Bad
message = "Version %s downloaded" % version

# ✅ Good
message = f"Version {version} downloaded"
```

5. ❌ **Not using enumerate**

```python
# ❌ Bad
for i in range(len(items)):
    print(i, items[i])

# ✅ Good
for i, item in enumerate(items):
    print(i, item)
```

## Project-Specific Conventions

### Workflow Handling

Always use the workflow normalization function:

```python
from avd_cli.constants import normalize_workflow

# Normalize legacy workflow names
workflow = normalize_workflow("full")  # Returns "eos-design"
workflow = normalize_workflow("config-only")  # Returns "cli-config"
```

### Constants

Use constants from `constants.py`:

```python
from avd_cli.constants import (
    DEFAULT_WORKFLOW,
    WORKFLOW_MAPPING,
    normalize_workflow,
)
```

### CLI Commands

Follow the standard pattern for Click commands. Use lazy imports for heavy dependencies to keep CLI startup fast (see Lazy Imports section above).

---

**Remember**: Code quality, type safety, and comprehensive testing are priorities in this project. Every piece of code should be production-ready, well-documented, and thoroughly tested.
