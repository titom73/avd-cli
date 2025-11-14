---
title: Device and Group Filtering with --limit Option
version: 1.0.0
date_created: 2025-11-13
date_updated: 2025-11-13
status: implemented
tags: [feature, cli, filtering, device-filter]
---

# Device and Group Filtering with --limit Option

## 1. Overview

### Purpose
The `--limit` option provides a unified filtering mechanism to select specific devices or groups of devices when executing AVD operations. This feature enables users to target operations to a subset of the inventory using hostname patterns or group name patterns, improving workflow efficiency and reducing execution time.

### Scope
This specification covers the `--limit` CLI option available across multiple commands:
- `avd-cli generate all`
- `avd-cli generate configs`
- `avd-cli generate docs`
- `avd-cli generate tests`
- `avd-cli deploy eos`

The filtering applies to device selection before any AVD operations are performed, ensuring only matching devices are processed.

### Context
Prior to this feature, the CLI provided `--limit-to-groups` which only supported filtering by group names. The enhanced `--limit` option replaces this functionality while maintaining backward compatibility and adding the ability to filter by individual hostnames.

## 2. Requirements

### Functional Requirements

**REQ-001: Hostname Filtering**
- The `--limit` option SHALL accept hostname patterns to filter devices by their hostname
- Hostname patterns SHALL support glob-style wildcards: `*`, `?`, `[...]`
- Multiple hostname patterns MAY be specified by repeating the `--limit` option
- Priority: HIGH

**REQ-002: Group Name Filtering**
- The `--limit` option SHALL accept group name patterns to filter devices by their inventory groups
- Group name patterns SHALL support glob-style wildcards: `*`, `?`, `[...]`
- When a group pattern matches, ALL devices belonging to that group SHALL be included
- Multiple group patterns MAY be specified by repeating the `--limit` option
- Priority: HIGH

**REQ-003: Pattern Matching Logic**
- The system SHALL use Python's `fnmatch` module for pattern matching
- Matching SHALL be case-sensitive
- An empty pattern SHALL NOT match any devices
- Priority: HIGH

**REQ-004: Union of Filters**
- When multiple `--limit` options are provided, the result SHALL be the union of all matching devices
- A device matching ANY pattern (hostname OR group) SHALL be included
- Duplicate devices SHALL be automatically deduplicated
- Priority: HIGH

**REQ-005: Backward Compatibility**
- The deprecated `--limit-to-groups` option SHALL continue to work
- `--limit-to-groups` SHALL be treated as an alias for `--limit` with group filtering
- A deprecation warning MAY be shown when `--limit-to-groups` is used
- Priority: HIGH

**REQ-006: Integration with Generate Commands**
- `generate all` SHALL apply filtering before generating configs, docs, and tests
- `generate configs` SHALL apply filtering before generating device configurations
- `generate docs` SHALL apply filtering before generating documentation
- `generate tests` SHALL apply filtering before generating test catalogs
- Priority: HIGH

**REQ-007: Integration with Deploy Commands**
- `deploy eos` SHALL apply filtering before deploying configurations
- Only filtered devices SHALL have their configurations deployed
- Priority: HIGH

**REQ-008: Error Handling - No Matches**
- When no devices match the filter patterns, the system SHALL exit with an error
- The error message SHALL clearly indicate that no devices were found
- The error message SHOULD suggest checking pattern syntax or inventory
- Exit code SHALL be non-zero
- Priority: HIGH

**REQ-009: Error Handling - Invalid Patterns**
- Invalid glob patterns SHALL be detected and reported
- The system SHALL validate patterns before attempting device filtering
- Priority: MEDIUM

**REQ-010: Performance**
- Pattern matching SHALL be performed efficiently without loading unnecessary data
- Filtering SHALL complete in linear time relative to inventory size: O(n)
- Priority: MEDIUM

**REQ-011: CLI Help Documentation**
- The `--help` output SHALL clearly document the `--limit` option
- Help text SHALL include examples of hostname and group filtering
- Help text SHALL mention glob pattern support
- Priority: MEDIUM

**REQ-012: Validation Integration**
- Device filtering SHALL occur BEFORE inventory validation
- Only filtered devices SHALL be validated by the schema validator
- Priority: MEDIUM

**REQ-013: Logging and Observability**
- The system SHALL log which patterns were applied
- The system SHALL log the count of matched devices
- Log level SHALL be INFO for normal operations
- Priority: LOW

**REQ-014: Short Option Alias**
- The short option `-l` SHALL be available as an alias for `--limit`
- Priority: MEDIUM

### Non-Functional Requirements

**NFR-001: Usability**
- Pattern syntax SHALL be intuitive and follow common glob conventions
- Error messages SHALL be clear and actionable

**NFR-002: Maintainability**
- Filtering logic SHALL be implemented in a dedicated utility module
- The implementation SHALL be testable in isolation from CLI commands

**NFR-003: Extensibility**
- The filtering mechanism SHALL be designed to support future enhancements (e.g., regex patterns, complex expressions)

## 3. Constraints and Assumptions

### Technical Constraints
- Must use Python 3.9+ for type hints (tested on 3.9, 3.10, 3.11, 3.12, 3.13)
- Must integrate with existing Click-based CLI framework
- Must work with pyavd's data structures and expectations
- Must maintain existing inventory YAML structure

### Business Constraints
- Must maintain backward compatibility with `--limit-to-groups`
- Must not break existing user workflows
- Must support both simple and complex inventory structures

### Assumptions
- Users are familiar with glob pattern syntax from shell usage
- Inventory group names and hostnames are unique and well-defined
- Inventory is loaded successfully before filtering is applied

## 4. Acceptance Criteria

### AC-001: Hostname Pattern - Exact Match
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`, `spine-1`
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** only `leaf-1a` configuration is generated

### AC-002: Hostname Pattern - Wildcard Suffix
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`, `leaf-2a`, `spine-1`
**When** user runs `avd-cli generate configs --limit "leaf-1*"`
**Then** configurations are generated for `leaf-1a` and `leaf-1b` only

### AC-003: Hostname Pattern - Wildcard Prefix
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`, `leaf-2a`
**When** user runs `avd-cli generate configs --limit "*-1a"`
**Then** configuration is generated for `leaf-1a` only

### AC-004: Hostname Pattern - Wildcard Middle
**Given** an inventory with devices: `leaf-dc1-1a`, `leaf-dc2-1a`, `spine-dc1-1`
**When** user runs `avd-cli generate configs --limit "leaf-*-1a"`
**Then** configurations are generated for `leaf-dc1-1a` and `leaf-dc2-1a`

### AC-005: Hostname Pattern - Question Mark
**Given** an inventory with devices: `leaf-1a`, `leaf-2a`, `leaf-10a`
**When** user runs `avd-cli generate configs --limit "leaf-?a"`
**Then** configurations are generated for `leaf-1a` and `leaf-2a` only

### AC-006: Hostname Pattern - Character Class
**Given** an inventory with devices: `leaf-1a`, `leaf-2a`, `leaf-3a`, `leaf-4a`
**When** user runs `avd-cli generate configs --limit "leaf-[12]a"`
**Then** configurations are generated for `leaf-1a` and `leaf-2a` only

### AC-007: Group Pattern - Exact Match
**Given** an inventory with group `LEAFS` containing `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit LEAFS`
**Then** configurations are generated for `leaf-1a` and `leaf-1b`

### AC-008: Group Pattern - Wildcard
**Given** an inventory with groups: `DC1_LEAFS`, `DC2_LEAFS`, `DC1_SPINES`
**When** user runs `avd-cli generate configs --limit "*_LEAFS"`
**Then** all devices from `DC1_LEAFS` and `DC2_LEAFS` are processed

### AC-009: Multiple Patterns - Union
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`, `spine-1`
**When** user runs `avd-cli generate configs --limit leaf-1a --limit spine-1`
**Then** configurations are generated for `leaf-1a` and `spine-1`

### AC-010: Multiple Patterns - Hostname and Group Mix
**Given** an inventory with device `spine-1` and group `LEAFS` containing `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit spine-1 --limit LEAFS`
**Then** configurations are generated for `spine-1`, `leaf-1a`, and `leaf-1b`

### AC-011: Multiple Patterns - Deduplication
**Given** device `leaf-1a` belongs to group `LEAFS`
**When** user runs `avd-cli generate configs --limit leaf-1a --limit LEAFS`
**Then** `leaf-1a` configuration is generated exactly once

### AC-012: No Match - Error
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit spine-*`
**Then** command exits with error "No devices matched the filter patterns"
**And** exit code is non-zero

### AC-013: Empty Pattern - No Match
**Given** any inventory
**When** user runs `avd-cli generate configs --limit ""`
**Then** command exits with error indicating no devices matched

### AC-014: Short Option Alias
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate configs -l leaf-1a`
**Then** configuration is generated for `leaf-1a`

### AC-015: Backward Compatibility - limit-to-groups
**Given** an inventory with group `LEAFS` containing `leaf-1a`
**When** user runs `avd-cli generate configs --limit-to-groups LEAFS`
**Then** configuration is generated for `leaf-1a`

### AC-016: Generate All Command
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate all --limit leaf-1a`
**Then** configs, docs, and tests are generated for `leaf-1a` only

### AC-017: Generate Configs Command
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** configuration file is generated for `leaf-1a` only

### AC-018: Generate Docs Command
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate docs --limit leaf-1a`
**Then** documentation is generated for `leaf-1a` only

### AC-019: Generate Tests Command
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate tests --limit leaf-1a`
**Then** test catalog is generated for `leaf-1a` only

### AC-020: Deploy EOS Command
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli deploy eos --limit leaf-1a`
**Then** configuration is deployed to `leaf-1a` only

### AC-021: Case Sensitivity - Hostname
**Given** an inventory with device `Leaf-1A`
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** no devices match (case-sensitive)

### AC-022: Case Sensitivity - Group
**Given** an inventory with group `Leafs`
**When** user runs `avd-cli generate configs --limit leafs`
**Then** no devices match (case-sensitive)

### AC-023: Special Characters in Names
**Given** an inventory with device `leaf-1a_backup`
**When** user runs `avd-cli generate configs --limit "leaf-1a_*"`
**Then** configuration is generated for `leaf-1a_backup`

### AC-024: Fabric Group Matching
**Given** device `leaf-1a` belongs to fabric `FABRIC_A`
**When** user runs `avd-cli generate configs --limit FABRIC_A`
**Then** configuration is generated for `leaf-1a`

### AC-025: Nested Group Matching
**Given** device `leaf-1a` belongs to group `DC1_LEAFS` which belongs to `LEAFS`
**When** user runs `avd-cli generate configs --limit DC1_LEAFS`
**Then** configuration is generated for `leaf-1a`

### AC-026: Multiple Wildcards
**Given** an inventory with devices: `leaf-dc1-pod1-1a`, `leaf-dc1-pod2-1a`
**When** user runs `avd-cli generate configs --limit "leaf-*-pod*-1a"`
**Then** configurations are generated for both devices

### AC-027: Logging - Pattern Applied
**Given** any inventory
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** logs show "Applying device filter: ['leaf-1a']"

### AC-028: Logging - Match Count
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit "leaf-*"`
**Then** logs show "Filtered to 2 devices"

### AC-029: Help Documentation - Long Option
**Given** user wants to know about filtering
**When** user runs `avd-cli generate configs --help`
**Then** help text shows `--limit` with description and examples

### AC-030: Help Documentation - Short Option
**Given** user wants to know about filtering
**When** user runs `avd-cli generate configs --help`
**Then** help text shows `-l` as alias for `--limit`

### AC-031: Performance - Large Inventory
**Given** an inventory with 1000 devices
**When** user runs `avd-cli generate configs --limit "leaf-*"`
**Then** filtering completes in less than 1 second

### AC-032: Integration - Schema Validation
**Given** an inventory with devices: `leaf-1a` (valid), `leaf-1b` (invalid)
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** only `leaf-1a` is validated and processed

### AC-033: Edge Case - All Devices Match
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit "*"`
**Then** configurations are generated for all devices

### AC-034: Edge Case - Single Device Inventory
**Given** an inventory with only device `leaf-1a`
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** configuration is generated for `leaf-1a`

### AC-035: Edge Case - Empty Inventory
**Given** an inventory with no devices
**When** user runs `avd-cli generate configs --limit "*"`
**Then** command exits with error indicating no devices in inventory

### AC-036: Hostname Priority Over Group
**Given** device `leaf-1a` and group `leaf-1a` both exist
**When** user runs `avd-cli generate configs --limit leaf-1a`
**Then** both device `leaf-1a` and all devices in group `leaf-1a` are processed

### AC-037: Whitespace Handling
**Given** an inventory with device `leaf-1a`
**When** user runs `avd-cli generate configs --limit " leaf-1a "`
**Then** whitespace is trimmed and device `leaf-1a` is matched

### AC-038: No Limit Option - All Devices
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`, `spine-1`
**When** user runs `avd-cli generate configs` (no `--limit`)
**Then** configurations are generated for all devices

### AC-039: Combination with Other Options
**Given** an inventory with devices: `leaf-1a`, `leaf-1b`
**When** user runs `avd-cli generate configs --limit leaf-1a --output-dir custom/`
**Then** configuration for `leaf-1a` is generated in `custom/` directory

## 5. User Stories

### US-001: Developer Testing Single Device
**As a** network automation developer
**I want to** generate configuration for a single device during development
**So that** I can quickly iterate and test changes without processing the entire inventory

**Acceptance Criteria:**
- Can filter by exact hostname
- Generation completes in seconds
- Only specified device files are created

### US-002: Operations Team Targeting Pod
**As a** network operations engineer
**I want to** deploy configurations to all devices in a specific pod
**So that** I can perform targeted rollouts without affecting other pods

**Acceptance Criteria:**
- Can filter by group name or pattern
- All devices in matching groups are processed
- Non-matching devices are unaffected

### US-003: CI/CD Pipeline Validation
**As a** CI/CD pipeline developer
**I want to** validate configurations for changed devices only
**So that** pipeline execution is fast and resource-efficient

**Acceptance Criteria:**
- Can filter by multiple hostnames
- Validation runs only on specified devices
- Pipeline completes faster than full validation

## 6. Technical Design

### Architecture Overview

The filtering mechanism is implemented through a dedicated `DeviceFilter` utility class that encapsulates all pattern matching logic. This class is instantiated by CLI commands and applied to the loaded inventory before any pyavd operations.

```
CLI Command (--limit patterns)
    ↓
DeviceFilter.from_patterns(patterns)
    ↓
inventory.filter_devices(device_filter)
    ↓
Filtered Inventory
    ↓
pyavd Operations (generate/deploy)
```

### Component: DeviceFilter Class

**Location:** `avd_cli/utils/device_filter.py`

**Responsibilities:**
- Parse and validate filter patterns
- Match patterns against device hostnames and groups
- Provide a clean interface for inventory filtering

**Interface:**

```python
from dataclasses import dataclass
from fnmatch import fnmatch

@dataclass
class DeviceFilter:
    """Filter for selecting devices by hostname or group patterns."""

    patterns: List[str]

    @classmethod
    def from_patterns(cls, patterns: Optional[List[str]]) -> Optional["DeviceFilter"]:
        """
        Create a DeviceFilter from CLI patterns.

        Args:
            patterns: List of glob patterns for hostnames or groups

        Returns:
            DeviceFilter instance if patterns provided, None otherwise
        """
        if not patterns:
            return None

        # Remove empty strings and strip whitespace
        clean_patterns = [p.strip() for p in patterns if p.strip()]

        if not clean_patterns:
            return None

        return cls(patterns=clean_patterns)

    def matches_hostname(self, hostname: str) -> bool:
        """
        Check if hostname matches any pattern.

        Args:
            hostname: Device hostname to check

        Returns:
            True if hostname matches any pattern
        """
        return any(fnmatch(hostname, pattern) for pattern in self.patterns)

    def matches_group(self, group: str) -> bool:
        """
        Check if group name matches any pattern.

        Args:
            group: Group name to check

        Returns:
            True if group matches any pattern
        """
        return any(fnmatch(group, pattern) for pattern in self.patterns)

    def matches_device(self, hostname: str, groups: List[str]) -> bool:
        """
        Check if device matches filter by hostname OR group membership.

        Args:
            hostname: Device hostname
            groups: List of groups device belongs to

        Returns:
            True if device matches by hostname or any group
        """
        # Check hostname match
        if self.matches_hostname(hostname):
            return True

        # Check group match
        return any(self.matches_group(group) for group in groups)
```

### Component: Inventory Filtering

**Location:** `avd_cli/models/inventory.py`

**Integration:**

```python
class AvdInventory:
    def filter_devices(self, device_filter: DeviceFilter | None) -> None:
        """
        Filter devices in inventory based on patterns.

        Args:
            device_filter: Filter to apply, None means no filtering

        Raises:
            ValueError: If no devices match the filter
        """
        if device_filter is None:
            return

        # Apply filter to each device
        filtered_devices = [
            device for device in self.devices
            if device_filter.matches_device(
                hostname=device.hostname,
                groups=device.groups + [device.fabric]
            )
        ]

        # Validate at least one device matched
        if not filtered_devices:
            raise ValueError(
                f"No devices matched the filter patterns: {device_filter.patterns}"
            )

        # Update inventory with filtered devices
        self.devices = filtered_devices
```

### Component: CLI Integration

**Location:** `avd_cli/cli/main.py`

**Click Option Definition:**

```python
import click

# Reusable option decorator
limit_option = click.option(
    "--limit", "-l",
    "limit_patterns",
    multiple=True,
    help=(
        "Filter devices by hostname or group name pattern. "
        "Supports glob wildcards: *, ?, [...]. "
        "Can be specified multiple times for union. "
        "Example: --limit 'leaf-*' --limit spine-1"
    )
)

# Deprecated option for backward compatibility
limit_to_groups_option = click.option(
    "--limit-to-groups",
    "limit_to_groups_patterns",
    multiple=True,
    hidden=True,  # Hide from help
    help="(Deprecated: use --limit instead) Filter devices by group name pattern."
)

@click.command()
@limit_option
@limit_to_groups_option
def generate_configs(limit_patterns, limit_to_groups_patterns, ...):
    """Generate device configurations."""

    # Merge limit patterns (backward compatibility)
    all_patterns = list(limit_patterns) + list(limit_to_groups_patterns)

    # Create filter
    device_filter = DeviceFilter.from_patterns(all_patterns)

    # Load inventory
    inventory = load_inventory(...)

    # Apply filter
    try:
        inventory.filter_devices(device_filter)
    except ValueError as e:
        raise click.ClickException(str(e))

    # Continue with filtered inventory
    ...
```

## 7. Data Model

### Input: CLI Patterns

```yaml
# Multiple patterns from CLI
patterns:
  - "leaf-1*"      # Glob pattern with wildcard
  - "spine-1"      # Exact hostname
  - "DC1_*"        # Group pattern
```

### Intermediate: DeviceFilter

```python
DeviceFilter(
    patterns=["leaf-1*", "spine-1", "DC1_*"]
)
```

### Output: Filtered Inventory

```python
AvdInventory(
    devices=[
        Device(hostname="leaf-1a", groups=["DC1_LEAFS"], ...),
        Device(hostname="leaf-1b", groups=["DC1_LEAFS"], ...),
        Device(hostname="spine-1", groups=["DC1_SPINES"], ...),
    ]
)
```

## 8. API Interfaces

### Public API: DeviceFilter

```python
class DeviceFilter:
    """
    Filter for selecting devices by hostname or group patterns.

    Attributes:
        patterns: List of glob patterns for matching
    """

    patterns: List[str]

    @classmethod
    def from_patterns(cls, patterns: Optional[List[str]]) -> Optional["DeviceFilter"]:
        """Create filter from CLI patterns."""
        ...

    def matches_hostname(self, hostname: str) -> bool:
        """Check if hostname matches any pattern."""
        ...

    def matches_group(self, group: str) -> bool:
        """Check if group matches any pattern."""
        ...

    def matches_device(self, hostname: str, groups: List[str]) -> bool:
        """Check if device matches by hostname or group."""
        ...
```

### Public API: AvdInventory

```python
class AvdInventory:
    """
    AVD inventory model.

    Attributes:
        devices: List of network devices
    """

    devices: List[Device]

    def filter_devices(self, device_filter: Optional[DeviceFilter]) -> None:
        """
        Filter devices in-place based on patterns.

        Args:
            device_filter: Filter to apply, None for no filtering

        Raises:
            ValueError: No devices matched the filter
        """
        ...
```

### CLI API: Click Options

```python
# Primary option
@click.option(
    "--limit", "-l",
    "limit_patterns",
    multiple=True,
    help="Filter devices by hostname or group name pattern"
)

# Deprecated option (backward compatibility)
@click.option(
    "--limit-to-groups",
    "limit_to_groups_patterns",
    multiple=True,
    hidden=True
)
```

## 9. Dependencies

### Internal Dependencies
- `avd_cli.models.inventory.AvdInventory` - Inventory data model
- `avd_cli.models.inventory.Device` - Device data model
- `avd_cli.logics.loader.load_inventory` - Inventory loading logic
- `avd_cli.cli.main` - CLI command definitions

### External Dependencies
- `click` (>=8.0) - CLI framework for option handling
- `fnmatch` (stdlib) - Glob pattern matching
- `typing` (stdlib) - Type hints

### Development Dependencies
- `pytest` (>=8.0) - Test framework
- `pytest-mock` - Mocking for tests

## 10. Test Strategy

### Unit Tests

**Location:** `tests/unit/utils/test_device_filter.py`

```python
import pytest
from avd_cli.utils.device_filter import DeviceFilter

class TestDeviceFilterCreation:
    def test_from_patterns_with_valid_patterns(self):
        """Test creating filter with valid patterns."""
        patterns = ["leaf-*", "spine-1"]
        filter = DeviceFilter.from_patterns(patterns)
        assert filter is not None
        assert filter.patterns == patterns

    def test_from_patterns_with_none(self):
        """Test creating filter with None returns None."""
        assert DeviceFilter.from_patterns(None) is None

    def test_from_patterns_with_empty_list(self):
        """Test creating filter with empty list returns None."""
        assert DeviceFilter.from_patterns([]) is None

    def test_from_patterns_strips_whitespace(self):
        """Test that whitespace is stripped from patterns."""
        patterns = [" leaf-* ", "  spine-1"]
        filter = DeviceFilter.from_patterns(patterns)
        assert filter.patterns == ["leaf-*", "spine-1"]

class TestHostnameMatching:
    def test_exact_match(self):
        """Test exact hostname match."""
        filter = DeviceFilter(patterns=["leaf-1a"])
        assert filter.matches_hostname("leaf-1a") is True
        assert filter.matches_hostname("leaf-1b") is False

    def test_wildcard_suffix(self):
        """Test wildcard at end of pattern."""
        filter = DeviceFilter(patterns=["leaf-*"])
        assert filter.matches_hostname("leaf-1a") is True
        assert filter.matches_hostname("leaf-1b") is True
        assert filter.matches_hostname("spine-1") is False

    def test_wildcard_prefix(self):
        """Test wildcard at start of pattern."""
        filter = DeviceFilter(patterns=["*-1a"])
        assert filter.matches_hostname("leaf-1a") is True
        assert filter.matches_hostname("spine-1a") is True
        assert filter.matches_hostname("leaf-1b") is False

    def test_question_mark(self):
        """Test single character wildcard."""
        filter = DeviceFilter(patterns=["leaf-?a"])
        assert filter.matches_hostname("leaf-1a") is True
        assert filter.matches_hostname("leaf-2a") is True
        assert filter.matches_hostname("leaf-10a") is False

    def test_character_class(self):
        """Test character class pattern."""
        filter = DeviceFilter(patterns=["leaf-[12]a"])
        assert filter.matches_hostname("leaf-1a") is True
        assert filter.matches_hostname("leaf-2a") is True
        assert filter.matches_hostname("leaf-3a") is False

class TestGroupMatching:
    def test_exact_group_match(self):
        """Test exact group name match."""
        filter = DeviceFilter(patterns=["LEAFS"])
        assert filter.matches_group("LEAFS") is True
        assert filter.matches_group("SPINES") is False

    def test_group_wildcard(self):
        """Test wildcard group match."""
        filter = DeviceFilter(patterns=["DC1_*"])
        assert filter.matches_group("DC1_LEAFS") is True
        assert filter.matches_group("DC1_SPINES") is True
        assert filter.matches_group("DC2_LEAFS") is False

class TestDeviceMatching:
    def test_matches_by_hostname(self):
        """Test device matches by hostname."""
        filter = DeviceFilter(patterns=["leaf-1a"])
        assert filter.matches_device("leaf-1a", ["LEAFS"]) is True

    def test_matches_by_group(self):
        """Test device matches by group."""
        filter = DeviceFilter(patterns=["LEAFS"])
        assert filter.matches_device("leaf-1a", ["LEAFS", "DC1"]) is True

    def test_no_match(self):
        """Test device does not match."""
        filter = DeviceFilter(patterns=["spine-*"])
        assert filter.matches_device("leaf-1a", ["LEAFS"]) is False
```

**Location:** `tests/unit/models/test_inventory_filtering.py`

```python
import pytest
from avd_cli.models.inventory import AvdInventory, Device
from avd_cli.utils.device_filter import DeviceFilter

class TestInventoryFiltering:
    def test_filter_by_hostname(self):
        """Test filtering devices by hostname pattern."""
        inventory = AvdInventory(devices=[
            Device(hostname="leaf-1a", groups=["LEAFS"]),
            Device(hostname="leaf-1b", groups=["LEAFS"]),
            Device(hostname="spine-1", groups=["SPINES"]),
        ])

        filter = DeviceFilter(patterns=["leaf-*"])
        inventory.filter_devices(filter)

        assert len(inventory.devices) == 2
        assert all(d.hostname.startswith("leaf-") for d in inventory.devices)

    def test_filter_by_group(self):
        """Test filtering devices by group pattern."""
        inventory = AvdInventory(devices=[
            Device(hostname="leaf-1a", groups=["LEAFS"]),
            Device(hostname="spine-1", groups=["SPINES"]),
        ])

        filter = DeviceFilter(patterns=["LEAFS"])
        inventory.filter_devices(filter)

        assert len(inventory.devices) == 1
        assert inventory.devices[0].hostname == "leaf-1a"

    def test_no_filter_applied(self):
        """Test that None filter does not change inventory."""
        original_devices = [
            Device(hostname="leaf-1a", groups=["LEAFS"]),
            Device(hostname="spine-1", groups=["SPINES"]),
        ]
        inventory = AvdInventory(devices=original_devices.copy())

        inventory.filter_devices(None)

        assert len(inventory.devices) == 2

    def test_no_matches_raises_error(self):
        """Test that no matches raises ValueError."""
        inventory = AvdInventory(devices=[
            Device(hostname="leaf-1a", groups=["LEAFS"]),
        ])

        filter = DeviceFilter(patterns=["spine-*"])

        with pytest.raises(ValueError, match="No devices matched"):
            inventory.filter_devices(filter)
```

### Integration Tests

**Location:** `tests/integration/test_device_filtering.py`

```python
import pytest
from click.testing import CliRunner
from avd_cli.cli.main import cli

class TestFilteringIntegration:
    def test_generate_configs_with_hostname_filter(self, tmp_path):
        """Test generate configs with hostname filter."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate", "configs",
            "-i", "examples/atd-inventory/inventory.yml",
            "--limit", "leaf-1a",
            "-o", str(tmp_path)
        ])

        assert result.exit_code == 0
        # Verify only leaf-1a config exists
        assert (tmp_path / "leaf-1a.cfg").exists()
        assert not (tmp_path / "leaf-1b.cfg").exists()

    def test_generate_configs_with_group_filter(self, tmp_path):
        """Test generate configs with group filter."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate", "configs",
            "-i", "examples/atd-inventory/inventory.yml",
            "--limit", "LEAFS",
            "-o", str(tmp_path)
        ])

        assert result.exit_code == 0
        # Verify all leaf configs exist
        assert (tmp_path / "leaf-1a.cfg").exists()
        assert (tmp_path / "leaf-1b.cfg").exists()
        # Verify spine configs do not exist
        assert not (tmp_path / "spine-1.cfg").exists()
```

### CLI Tests

**Location:** `tests/unit/cli/test_limit_option.py`

```python
import pytest
from click.testing import CliRunner
from avd_cli.cli.main import generate_configs

class TestLimitOption:
    def test_limit_option_present_in_help(self):
        """Test that --limit appears in help."""
        runner = CliRunner()
        result = runner.invoke(generate_configs, ["--help"])
        assert "--limit" in result.output
        assert "-l" in result.output

    def test_multiple_limit_patterns(self):
        """Test specifying multiple limit patterns."""
        # This would be tested via integration test
        pass
```

### Test Coverage Goals
- Unit tests: >95% coverage on DeviceFilter class
- Unit tests: >90% coverage on inventory filtering logic
- Integration tests: All CLI commands with --limit option
- Edge cases: Empty patterns, no matches, all matches

## 11. Examples and Use Cases

### Example 1: Filter Single Device

```bash
# Generate config for specific device
avd-cli generate configs -i inventory.yml --limit leaf-1a

# Short form
avd-cli generate configs -i inventory.yml -l leaf-1a
```

### Example 2: Filter Multiple Devices with Wildcard

```bash
# All leaf switches in rack 1
avd-cli generate configs -i inventory.yml --limit "leaf-1*"

# Expected: leaf-1a, leaf-1b, leaf-1c
```

### Example 3: Filter by Group

```bash
# All devices in LEAFS group
avd-cli generate configs -i inventory.yml --limit LEAFS

# All leaf groups across data centers
avd-cli generate configs -i inventory.yml --limit "*_LEAFS"
```

### Example 4: Multiple Patterns (Union)

```bash
# Specific spine and all leafs
avd-cli generate configs -i inventory.yml \
  --limit spine-1 \
  --limit "leaf-*"
```

### Example 5: Deploy to Filtered Devices

```bash
# Deploy config to single device
avd-cli deploy eos -i inventory.yml --limit leaf-1a

# Deploy to group
avd-cli deploy eos -i inventory.yml --limit DC1_LEAFS
```

### Example 6: Generate All with Filter

```bash
# Generate configs, docs, and tests for filtered devices
avd-cli generate all -i inventory.yml --limit "leaf-1*"
```

### Example 7: CI/CD Use Case

```bash
# In CI pipeline, generate only for changed devices
CHANGED_DEVICES="leaf-1a leaf-2a spine-1"

for device in $CHANGED_DEVICES; do
  avd-cli generate configs -i inventory.yml --limit "$device"
done
```

## 12. Error Handling

### Error Scenarios

**No Devices Match Filter**
```
Error: No devices matched the filter patterns: ['spine-*']
Suggestion: Check pattern syntax or verify devices exist in inventory
```

**Empty Inventory**
```
Error: No devices found in inventory
```

**Invalid Pattern (Future Enhancement)**
```
Error: Invalid glob pattern: '[unclosed'
```

## 13. Monitoring and Logging

### Log Messages

**INFO Level:**
```
Applying device filter: ['leaf-1*', 'spine-1']
Filtered to 3 devices: leaf-1a, leaf-1b, spine-1
```

**DEBUG Level:**
```
Checking device 'leaf-1a' against patterns ['leaf-1*']
  Hostname 'leaf-1a' matches pattern 'leaf-1*': True
Device 'leaf-1a' included in filter
```

**ERROR Level:**
```
No devices matched filter patterns: ['invalid-*']
Total devices in inventory: 10
```

## 14. Migration and Rollout

### Backward Compatibility

The deprecated `--limit-to-groups` option remains functional:

```bash
# Old way (still works)
avd-cli generate configs --limit-to-groups LEAFS

# New way (recommended)
avd-cli generate configs --limit LEAFS
```

### Migration Path

**Phase 1: Introduction (Current)**
- `--limit` option introduced
- `--limit-to-groups` continues to work (hidden from help)
- Documentation updated to use `--limit`

**Phase 2: Deprecation Warning (Future)**
- Add warning message when `--limit-to-groups` is used
- Update all examples and tutorials

**Phase 3: Removal (Future Major Version)**
- Remove `--limit-to-groups` option entirely
- Breaking change announced in release notes

## 15. Open Questions and Future Enhancements

### Resolved Questions
✅ Should filtering be case-sensitive? **Decision: Yes, follow Unix conventions**
✅ Should --limit replace --limit-to-groups? **Decision: Yes, with backward compatibility**
✅ Should fabric be included in group matching? **Decision: Yes**

### Future Enhancements

**FE-001: Regex Pattern Support**
- Allow regex patterns for complex matching
- Syntax: `--limit-regex '^leaf-[0-9]+a$'`

**FE-002: Exclusion Patterns**
- Allow excluding devices from matches
- Syntax: `--limit 'leaf-*' --exclude 'leaf-1*'`

**FE-003: Interactive Selection**
- Provide interactive device picker
- Syntax: `--limit --interactive`

**FE-004: Filter by Device Properties**
- Filter by device type, role, platform
- Syntax: `--limit-by type=leaf`

**FE-005: Save/Load Filter Sets**
- Save commonly used filter patterns
- Syntax: `--limit @production-leafs`

## 16. Glossary

**Device**: A network device (switch, router) defined in the inventory
**Fabric**: Top-level group representing a network fabric
**Glob Pattern**: Pattern syntax using *, ?, [...] for matching (e.g., shell wildcards)
**Group**: Logical collection of devices in the inventory hierarchy
**Hostname**: Unique identifier for a device
**Pattern**: String with wildcards used for matching
**Union**: Set operation combining results from multiple patterns

## 17. References

- [fnmatch documentation](https://docs.python.org/3/library/fnmatch.html)
- [Click documentation - Options](https://click.palletsprojects.com/en/stable/options/)
- [AVD Inventory Schema](./data-avd-inventory-schema.md)
- [PR #21: Extend --limit feature](https://github.com/titom73/avd-cli/pull/21)

## 18. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-13 | System | Initial specification for --limit feature |

---

*This specification is a living document and will be updated as the feature evolves.*
