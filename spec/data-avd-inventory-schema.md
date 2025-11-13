---
title: AVD Inventory Data Schema Specification
version: 1.5
date_created: 2025-11-06
last_updated: 2025-01-19
owner: AVD CLI Development Team
tags: [data, schema, avd, inventory, validation, jinja2, templating, mpls, multi-design]
---

# Introduction

This specification defines the data schema requirements for AVD inventory structures, validation rules, and data contracts that the AVD CLI tool must support when processing Arista AVD inventories.

**Version 1.5 Updates (2025-01-19):**

This revision extends the specification to support multiple AVD design types beyond the traditional L3LS-EVPN spine/leaf architecture:

- **Multi-Design Support**: Added support for MPLS, L2LS, and custom design types
- **Dynamic Node Type Discovery**: Inventory loader now discovers node type keys dynamically (e.g., "p", "pe" for MPLS; "spine", "leaf" for L3LS-EVPN)
- **Flexible Device Organization**: `FabricDefinition` now uses `devices_by_type: Dict[str, List[DeviceDefinition]]` instead of hardcoded `spine_devices`/`leaf_devices` fields
- **Design-Agnostic Validation**: Topology validation is now design-aware (e.g., MPLS doesn't require spine devices)
- **MPLS Example Support**: Added comprehensive examples and tests for MPLS design with P (provider) and PE (provider edge) routers
- **Custom Node Types**: Full support for user-defined node types via `custom_node_type_keys` and dynamic discovery

These changes ensure that `avd-cli` works seamlessly with:
- `examples/eos-design-complex` (L3LS-EVPN design with spine/leaf)
- `examples/eos-design-mpls` (MPLS design with P/PE routers)
- User inventories with custom node type definitions

## 1. Purpose & Scope

### Purpose

Define the data structures, validation rules, and constraints for AVD inventory processing to ensure:

- Consistent inventory validation
- Clear error messages for invalid data
- Type-safe data handling throughout the application
- Compatibility with py-avd library expectations

### Scope

- AVD inventory directory structure requirements
- YAML data schema for group_vars and host_vars
- Required and optional field definitions
- Data validation rules and error handling
- Type definitions for internal data models

### Audience

- Developers implementing inventory loading and validation
- AI coding assistants generating data handling code
- Users creating or troubleshooting AVD inventories
- Integration developers

### Assumptions

- Inventory follows Ansible directory structure conventions
- YAML files follow standard YAML 1.2 specification
- py-avd library defines the canonical AVD schema

## 2. Definitions

- **Inventory Root**: Top-level directory containing AVD inventory
- **group_vars**: Directory containing group-level variable definitions
- **host_vars**: Directory containing host-level variable definitions
- **Fabric**: Collection of network devices forming a network topology
- **Device Role**: Type of device (spine, leaf, border_leaf, etc.)
- **Design Type**: AVD network architecture pattern (l3ls-evpn, mpls, l2ls) that defines the routing protocols and topology structure
- **Node Type**: Category of network device within a design (e.g., spine, leaf for l3ls-evpn; p, pe for mpls)
- **Standard Node Types**: Default node type keys provided by each AVD design (e.g., spine, l3leaf, l2leaf for l3ls-evpn)
- **Custom Node Types**: User-defined node type keys in inventory via custom_node_type_keys or direct definition in group_vars (e.g., wan_edge, core_router)
- **Structured Config**: Hierarchical configuration data structure
- **Schema Validation**: Process of verifying data against defined rules
- **Custom Structured Configuration**: User-defined configuration that extends or overrides AVD-generated structured configs
- **Schema Extension**: Mechanism to add custom device types and platform configurations beyond default AVD schema
- **Type Mapping**: Process of translating AVD device types (l3spine, l2leaf) to canonical types (spine, leaf)
- **Jinja2 Template**: Dynamic template syntax using `{{ variable }}` notation for variable substitution
- **Template Variable**: Variable reference in Jinja2 format that is resolved at runtime from inventory context
- **hostvars**: Ansible special variable containing all variables for all hosts in the inventory
- **Template Filter**: Jinja2 filter applied to variables (e.g., `| default(value)`, `| lower`, `| upper`)

## 3. Requirements, Constraints & Guidelines

### Data Structure Requirements

- **REQ-001**: Inventory root shall contain group_vars and/or host_vars directories
- **REQ-002**: YAML files shall be valid YAML 1.2 format
- **REQ-003**: All device definitions shall include required fields
- **REQ-004**: Group inheritance shall follow Ansible precedence rules
- **REQ-005**: Variable names shall follow Python identifier rules
- **REQ-006**: IP addresses shall be valid IPv4 or IPv6 format
- **REQ-007**: Platform names shall match supported EOS platforms
- **REQ-008**: group_vars and host_vars shall support both file and directory formats
- **REQ-009**: When group_vars/host_vars entry is a directory, all YAML files within shall be loaded and merged
- **REQ-010**: Directory-based variables shall be merged in alphabetical filename order
- **REQ-011**: Application shall support AVD device type aliases (l3spine → spine, l2leaf → leaf)
- **REQ-012**: Application shall allow custom device types via configuration
- **REQ-013**: Application shall support custom_structured_configuration for schema extensions
- **REQ-014**: Custom structured configurations shall be merged with device definitions
- **REQ-015**: Application shall support Jinja2 template syntax for variable references in YAML values
- **REQ-016**: Application shall resolve `{{ variable }}` references from inventory context
- **REQ-017**: Application shall support hostvars dictionary access pattern: `{{ hostvars['hostname']['variable'] }}`
- **REQ-018**: Application shall support Jinja2 filters: `{{ variable | default(value) }}`, `{{ variable | lower }}`, etc.
- **REQ-019**: Template resolution shall occur after all YAML files are loaded but before validation
- **REQ-020**: Unresolved template variables shall be handled gracefully with clear error messages
- **REQ-021**: Application shall support multiple AVD design types: l3ls-evpn, mpls, l2ls
- **REQ-022**: Application shall discover node type keys dynamically from inventory data, where each design type provides a standard list of node types (e.g., spine/l3leaf/l2leaf for l3ls-evpn; p/pe for mpls) and users can define additional custom node types in group_vars
- **REQ-023**: Application shall not assume spine/leaf topology exists for all design types
- **REQ-024**: Application shall support design-specific standard node types defined per design (spine/l3leaf/l2leaf/border_leaf for l3ls-evpn; p/pe for mpls; l2spine/l2leaf for l2ls) and allow custom node type definitions via custom_node_type_keys
- **REQ-025**: Application shall handle inventories with "type" variable defining device roles (e.g., vars: type: "pe")

### Validation Requirements

- **VAL-001**: Schema validation shall occur before processing
- **VAL-002**: Validation errors shall include file path and line number
- **VAL-003**: Missing required fields shall be reported clearly
- **VAL-004**: Type mismatches shall be caught during validation
- **VAL-005**: Cross-references (e.g., peer links) shall be validated
- **VAL-006**: Duplicate definitions shall be detected and reported

### Data Type Requirements

- **TYP-001**: All data models shall use Python dataclasses or Pydantic models
- **TYP-002**: All fields shall have explicit type annotations
- **TYP-003**: Optional fields shall use Optional[T] or T | None
- **TYP-004**: Collections shall use List, Dict, Set from typing module
- **TYP-005**: Custom types shall be defined for domain concepts

### Schema Integration Requirements

- **INT-001**: Application shall load AVD schema constants from py-avd library where available
- **INT-002**: Platform names shall be sourced from pyavd._eos_designs.schema module
- **INT-003**: Device types shall be sourced from pyavd._eos_designs.schema module
- **INT-004**: Application shall gracefully fallback to hardcoded constants if py-avd unavailable
- **INT-005**: Schema constants shall be cached after initial load to avoid repeated imports
- **INT-006**: Application shall recognize AVD-specific device type aliases and map them to canonical types
- **INT-007**: Custom structured configurations shall be loaded from group_vars and merged per AVD conventions
- **INT-008**: Jinja2 templating shall integrate with py-avd's template rendering if available
- **INT-009**: Application shall use Jinja2 library (version >=3.0) for template processing

### Constraints

- **CON-001**: Must support inventories with up to 1000 devices
- **CON-002**: Must handle YAML files up to 10MB in size
- **CON-003**: Must validate inventory in <2 seconds for typical size
- **CON-004**: Must maintain backward compatibility with AVD schema versions
- **CON-005**: Maximum directory depth for group_vars/host_vars: 1 level (no recursive subdirectories)
- **CON-006**: Maximum number of YAML files per group/host directory: 50 files

### Patterns

- **PAT-001**: Variable Loading Pattern - Load group_vars and host_vars recursively following Ansible precedence
- **PAT-002**: Directory Merge Pattern - When loading directory, merge all YAML files in alphabetical order
- **PAT-003**: File Discovery Pattern - Check if path is file (.yml/.yaml) or directory, handle accordingly
- **PAT-004**: Deep Merge Pattern - Merge dictionaries recursively, later values override earlier ones
- **PAT-005**: Type Mapping Pattern - Map AVD device types to canonical types (l3spine→spine, l2leaf→leaf)
- **PAT-006**: Schema Extension Pattern - Allow custom device types and platform settings via custom_structured_configuration
- **PAT-007**: Template Resolution Pattern - Recursively walk data structures and resolve Jinja2 templates in string values
- **PAT-008**: Context Building Pattern - Build Jinja2 context from global_vars, group_vars, and host_vars with proper precedence

### Device Type Mapping Requirements

- **DTM-001**: Application shall maintain a mapping table for AVD device type aliases to canonical types
- **DTM-002**: Mapping shall include: l3spine → spine, l2leaf → leaf, l3leaf → leaf
- **DTM-003**: Application shall support custom node types defined in inventory (e.g., "p", "pe" for MPLS design)
- **DTM-004**: Unknown types shall be accepted with validation mode: strict mode (error) or permissive mode (warning)
- **DTM-005**: Application shall detect node type definitions from inventory data (keys like "p:", "pe:", custom_node_type_keys)
- **DTM-006**: Application shall categorize devices by their inventory-defined type without forcing spine/leaf classification

### Design-Specific Node Type Requirements

- **DNT-001**: Application shall recognize standard node types per design: l3ls-evpn (spine, l3leaf, l2leaf, border_leaf), mpls (p, pe), l2ls (l2spine, l2leaf)
- **DNT-002**: Application shall support custom_node_type_keys for defining additional node types beyond standard ones
- **DNT-003**: Application shall allow users to define custom node type keys directly in group_vars (e.g., "wan_edge:", "core_router:")
- **DNT-004**: Application shall not restrict node type discovery to a predefined list, allowing any key with topology structure (defaults, nodes, node_groups)
- **DNT-005**: Standard node types for each design shall be used for validation and type-specific processing when design_type is detected
- **DNT-006**: Custom node types shall be treated equivalently to standard node types in device organization and filtering

### Custom Structured Configuration Requirements

- **CSC-001**: Application shall support custom_structured_configuration key in group_vars
- **CSC-002**: Custom structured configs shall support platform-specific settings via custom_structured_platform_settings
- **CSC-003**: Platform settings shall be matched against device platform and applied accordingly
- **CSC-004**: Custom configs shall be deep-merged with device definitions (custom overrides base)
- **CSC-005**: Custom structured configs shall follow AVD schema conventions for compatibility

### Jinja2 Template Variable Requirements

- **TPL-001**: Application shall detect Jinja2 template syntax in string values: `{{ ... }}`
- **TPL-002**: Template resolution shall support variable references from inventory context
- **TPL-003**: Template context shall include: global_vars, group_vars, host_vars, and hostvars dictionary
- **TPL-004**: Application shall support hostvars access: `{{ hostvars['hostname']['variable'] }}`
- **TPL-005**: Application shall support Jinja2 filters: default, lower, upper, replace, etc.
- **TPL-006**: Application shall handle filter syntax: `{{ variable | filter_name(args) }}`
- **TPL-007**: Undefined variables shall raise clear errors indicating missing variable name
- **TPL-008**: Template resolution shall occur recursively on all string values in loaded YAML
- **TPL-009**: Application shall preserve non-string types during template resolution
- **TPL-010**: Template errors shall include source file path and variable name for debugging

### Guidelines

- **GUD-001**: Use descriptive variable names matching AVD conventions
- **GUD-002**: Organize variables by logical grouping
- **GUD-003**: Document custom variables with inline comments
- **GUD-004**: Use YAML anchors and aliases for repeated structures
- **GUD-005**: Keep individual YAML files focused and modular
- **GUD-006**: Prefer directory format for groups with many variables (>100 lines)
- **GUD-007**: Use alphabetically ordered filenames for predictable merge order
- **GUD-008**: Group related variables in same file within directory (e.g., aaa.yml, ntp.yml, snmp.yml)
- **GUD-009**: Use custom_structured_configuration for schema extensions rather than modifying core schemas
- **GUD-010**: Document custom device types and their mapping to canonical types in README
- **GUD-011**: Use Jinja2 templates for referencing variables to avoid duplication
- **GUD-012**: Always provide default values with `| default()` filter for optional variables
- **GUD-013**: Document all variables that are referenced via Jinja2 templates
- **GUD-014**: Prefer simple variable references over complex Jinja2 expressions for maintainability

## 4. Interfaces & Data Contracts

### Inventory Directory Structure

The inventory loader shall support two formats for group_vars and host_vars:

1. **File Format**: Single YAML file per group/host
2. **Directory Format**: Directory containing multiple YAML files that are merged

#### File Format (Simple)

```text
inventory/
├── group_vars/
│   ├── all.yml                    # Global variables
│   ├── FABRIC.yml                 # Fabric-wide settings
│   ├── SPINES.yml                 # Spine group variables
│   ├── LEAFS.yml                  # Leaf group variables
│   └── BORDER_LEAFS.yml           # Border leaf variables
├── host_vars/
│   ├── spine1.yml                 # Individual device variables
│   ├── spine2.yml
│   ├── leaf1.yml
│   └── leaf2.yml
├── inventory.yml                  # Inventory hosts definition
└── ansible.cfg                    # Optional Ansible configuration
```

#### Directory Format (Modular)

```text
inventory/
├── group_vars/
│   ├── all/                       # Global variables directory
│   │   ├── basics.yml             # Basic configuration
│   │   ├── aaa.yml                # AAA settings
│   │   └── ntp.yml                # NTP configuration
│   ├── FABRIC.yml                 # Fabric-wide settings (file format)
│   ├── SPINES/                    # Spine group variables directory
│   │   ├── topology.yml           # Topology definition
│   │   └── bgp.yml                # BGP configuration
│   └── LEAFS/                     # Leaf group variables directory
│       ├── topology.yml           # Topology definition
│       ├── interfaces.yml         # Interface profiles
│       └── services.yml           # Services configuration
├── host_vars/
│   ├── spine1/                    # Individual device directory
│   │   ├── system.yml             # System-specific overrides
│   │   └── interfaces.yml         # Interface overrides
│   ├── spine2.yml                 # Or single file format
│   └── leaf1.yml
├── inventory.yml                  # Inventory hosts definition
└── ansible.cfg                    # Optional Ansible configuration
```

#### Mixed Format (Supported)

The loader shall support mixing file and directory formats within the same inventory:

```text
inventory/
├── group_vars/
│   ├── all/                       # Directory with multiple files
│   │   ├── basics.yml
│   │   └── platform.yml
│   ├── FABRIC.yml                 # Single file
│   └── SPINES/                    # Directory with multiple files
│       ├── topology.yml
│       └── bgp.yml
└── host_vars/
    ├── spine1/                    # Directory
    │   └── overrides.yml
    └── spine2.yml                 # Single file
```

### Core Data Models

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from ipaddress import IPv4Address, IPv6Address

@dataclass
class DeviceDefinition:
    """Core device definition data model."""

    # Required fields
    hostname: str
    platform: str
    mgmt_ip: IPv4Address | IPv6Address
    device_type: str  # spine, leaf, border_leaf, etc.

    # Network topology
    fabric: str
    pod: Optional[str] = None
    rack: Optional[str] = None

    # Optional fields with defaults
    mgmt_gateway: Optional[IPv4Address] = None
    serial_number: Optional[str] = None
    system_mac_address: Optional[str] = None

    # AVD-specific
    structured_config: Dict[str, Any] = field(default_factory=dict)
    custom_variables: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate device definition after initialization."""
        self._validate_hostname()
        self._validate_platform()
        self._validate_device_type()

    def _validate_hostname(self) -> None:
        """Validate hostname format."""
        if not self.hostname:
            raise ValueError("Hostname cannot be empty")
        if not self.hostname.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid hostname format: {self.hostname}")

    def _validate_platform(self) -> None:
        """Validate platform is supported.

        Platform list is dynamically loaded from py-avd schema where possible.
        Falls back to hardcoded list if py-avd is unavailable.
        """
        from avd_cli.utils.schema import get_supported_platforms

        supported_platforms = get_supported_platforms()
        if self.platform not in supported_platforms:
            raise ValueError(
                f"Unsupported platform: {self.platform}. "
                f"Supported: {', '.join(sorted(supported_platforms))}"
            )

    def _validate_device_type(self) -> None:
        """Validate device type.

        Device type list is dynamically loaded from py-avd schema where possible.
        Falls back to hardcoded list if py-avd is unavailable.
        """
        from avd_cli.utils.schema import get_supported_device_types

        valid_types = get_supported_device_types()
        if self.device_type not in valid_types:
            raise ValueError(
                f"Invalid device type: {self.device_type}. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )

@dataclass
class FabricDefinition:
    """Fabric topology definition.
    
    Uses flexible device dictionary to support any AVD design type.
    """

    name: str
    design_type: str  # l3ls-evpn, mpls, l2ls, etc.
    devices_by_type: Dict[str, List[DeviceDefinition]] = field(default_factory=dict)

    # Fabric-wide settings
    bgp_asn_range: Optional[str] = None
    mlag_peer_l3_vlan: int = 4093
    mlag_peer_vlan: int = 4094

    # Backward compatibility properties
    @property
    def spine_devices(self) -> List[DeviceDefinition]:
        """Get spine devices (backward compatibility)."""
        return self.devices_by_type.get("spine", [])

    @property
    def leaf_devices(self) -> List[DeviceDefinition]:
        """Get leaf devices (backward compatibility)."""
        return self.devices_by_type.get("leaf", [])

    @property
    def border_leaf_devices(self) -> List[DeviceDefinition]:
        """Get border leaf devices (backward compatibility)."""
        return self.devices_by_type.get("border_leaf", [])

    def get_all_devices(self) -> List[DeviceDefinition]:
        """Get all devices in fabric across all types."""
        all_devices = []
        for device_list in self.devices_by_type.values():
            all_devices.extend(device_list)
        return all_devices

    def get_devices_by_type(self, device_type: str) -> List[DeviceDefinition]:
        """Get devices filtered by type."""
        return self.devices_by_type.get(device_type, [])

@dataclass
class InventoryData:
    """Complete inventory data structure."""

    root_path: Path
    fabrics: List[FabricDefinition] = field(default_factory=list)
    global_vars: Dict[str, Any] = field(default_factory=dict)

    def get_all_devices(self) -> List[DeviceDefinition]:
        """Get all devices across all fabrics."""
        devices = []
        for fabric in self.fabrics:
            devices.extend(fabric.get_all_devices())
        return devices

    def get_device_by_hostname(self, hostname: str) -> Optional[DeviceDefinition]:
        """Find device by hostname."""
        for device in self.get_all_devices():
            if device.hostname == hostname:
                return device
        return None

    def validate(self, skip_topology_validation: bool = False) -> List[str]:
        """Validate complete inventory structure.
        
        Parameters
        ----------
        skip_topology_validation : bool
            If True, skip design-specific topology checks (e.g., spine presence).
            Useful for non-L3LS-EVPN designs like MPLS.
        """
        errors = []

        # Check for duplicate hostnames
        hostnames = [d.hostname for d in self.get_all_devices()]
        duplicates = [h for h in hostnames if hostnames.count(h) > 1]
        if duplicates:
            errors.append(f"Duplicate hostnames found: {set(duplicates)}")

        # Check for duplicate management IPs
        mgmt_ips = [str(d.mgmt_ip) for d in self.get_all_devices()]
        duplicate_ips = [ip for ip in mgmt_ips if mgmt_ips.count(ip) > 1]
        if duplicate_ips:
            errors.append(f"Duplicate management IPs: {set(duplicate_ips)}")

        # Validate topology only for designs that require specific structure
        if not skip_topology_validation:
            for fabric in self.fabrics:
                # Only validate spine presence for L3LS-EVPN design
                if fabric.design_type == "l3ls-evpn" and not fabric.spine_devices:
                    errors.append(f"Fabric {fabric.name} (l3ls-evpn) has no spine devices")
                
                # For MPLS, validate P or PE routers exist
                if fabric.design_type == "mpls":
                    all_devices = fabric.get_all_devices()
                    if not all_devices:
                        errors.append(f"Fabric {fabric.name} (mpls) has no devices")

        return errors
```

### YAML Schema Examples

#### Group Variables (group_vars/FABRIC.yml)

```yaml
---
# Fabric name and design
fabric_name: DC1_FABRIC
design:
  type: l3ls-evpn

# BGP configuration
bgp_peer_groups:
  ipv4_underlay_peers:
    name: IPv4-UNDERLAY-PEERS
    password: "AQQvKeimxJu+uGQ/yYvv9w=="
  evpn_overlay_peers:
    name: EVPN-OVERLAY-PEERS
    password: "q+VNViP5i4rVjW1cxFv2wA=="

# Spine configuration
spine:
  defaults:
    platform: vEOS-lab
    bgp_as: 65001
    loopback_ipv4_pool: 192.168.255.0/24

  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
    - name: spine2
      id: 2
      mgmt_ip: 192.168.0.11/24

# Leaf configuration
leaf:
  defaults:
    platform: vEOS-lab
    bgp_as: 65100-65199
    loopback_ipv4_pool: 192.168.255.0/24
    vtep_loopback_ipv4_pool: 192.168.254.0/24
    mlag_peer_ipv4_pool: 10.255.252.0/24
    mlag_peer_l3_ipv4_pool: 10.255.251.0/24
    spanning_tree_mode: mstp
    spanning_tree_priority: 16384

  node_groups:
    - group: RACK1
      bgp_as: 65101
      nodes:
        - name: leaf1
          id: 1
          mgmt_ip: 192.168.0.12/24
        - name: leaf2
          id: 2
          mgmt_ip: 192.168.0.13/24
```

#### Host Variables (host_vars/spine1.yml)

```yaml
---
# Host-specific overrides for spine1
type: spine

# Management interface
mgmt_interface: Management1
mgmt_gateway: 192.168.0.1

# Specific platform if different from group default
# platform: 7280R3

# Custom structured configuration
structured_config:
  router_bgp:
    maximum_paths:
      paths: 4
      ecmp: 4
```

#### Custom Structured Configuration (group_vars/FABRIC/custom_configs.yml)

Custom structured configurations allow extending the AVD schema with user-defined settings that are merged into device configurations. See [AVD Custom Structured Configuration Guide](https://avd.arista.com/devel/ansible_collections/arista/avd/roles/eos_designs/docs/how-to/custom-structured-configuration.html).

```yaml
---
# Custom structured platform settings
custom_structured_platform_settings:
  # Platform-specific settings for 7050X3
  - feature_support:
      queue_monitor_length_notify: false
    platforms:
      - 7050X3
    management_interface: Management1
    reload_delay:
      mlag: 300
      non_mlag: 330
    trident_forwarding_table_partition: flexible exact-match 16384 l2-shared 98304 l3-shared 131072
    default_interface_mtu: 9214

  # Platform-specific settings for campus switches (720XP, 722XP)
  - feature_support:
      poe: true
      interface_storm_control: true
      per_interface_mtu: true
      queue_monitor_length_notify: false
    platforms:
      - 720XP
      - 720DP
      - 722XP
    reload_delay:
      mlag: 300
      non_mlag: 330
    management_interface: Management1
    default_interface_mtu: 1500

  # Platform-specific settings for cEOS
  - feature_support:
      bgp_update_wait_for_convergence: false
      bgp_update_wait_install: false
      evpn_gateway_all_active_multihoming: true
      interface_storm_control: false
      queue_monitor_length_notify: false
    management_interface: Management0
    platforms:
      - CEOS
      - cEOS
      - ceos
      - cEOSLab
    reload_delay:
      mlag: 300
      non_mlag: 330
    default_interface_mtu: 1500

# Custom structured configuration for all devices
custom_structured_configuration:
  # Global logging settings
  logging:
    console: informational
    monitor: debugging
    buffered:
      size: 10000
      level: debugging

  # Custom VLANs
  vlans:
    - id: 4000
      name: CUSTOM_VLAN
      trunk_groups:
        - MLAG
```

#### Device Type Mapping Example (L3LS-EVPN Design)

AVD uses specific device type names that map to canonical types for L3LS-EVPN design:

```yaml
---
# group_vars/SPINES.yml - Using AVD-specific type
l3spine:
  defaults:
    platform: 7050X3
    bgp_as: 65001
  node_groups:
    - group: DC1_SPINES
      nodes:
        - name: spine01
          id: 1
          mgmt_ip: 192.168.0.10/24

# This maps internally to canonical type: spine
# Application must recognize: l3spine → spine
```

**L3LS-EVPN Device Type Mapping Table:**

| AVD Type | Canonical Type | Description |
|----------|---------------|-------------|
| `l3spine` | `spine` | Layer 3 spine in EVPN fabric |
| `l2leaf` | `leaf` | Layer 2 access leaf |
| `l3leaf` | `leaf` | Layer 3 leaf with routing |
| `spine` | `spine` | Generic spine (canonical) |
| `leaf` | `leaf` | Generic leaf (canonical) |
| `border_leaf` | `border_leaf` | Border leaf for DCI |
| `super_spine` | `super_spine` | Super spine in large fabrics |
| `overlay_controller` | `overlay_controller` | Route reflector/controller |
| `wan_router` | `wan_router` | WAN edge router |

#### MPLS Design Type Support

MPLS design uses different node types than L3LS-EVPN. Instead of spine/leaf, it uses provider (P) and provider edge (PE) routers.

**MPLS Inventory Example (eos-design-mpls)**:

```yaml
---
# inventory.yml - MPLS design with P and PE routers
all:
  children:
    backbone:
      children:
        backbone_p_routers:
          vars:
            type: "p"  # Provider router type
          hosts:
            s1-p01:
              ansible_host: 192.168.2.111
            s2-p01:
              ansible_host: 192.168.2.121
        backbone_pe_routers:
          vars:
            type: "pe"  # Provider edge router type
          hosts:
            s1-pe01:
              ansible_host: 192.168.2.11
            s1-pe02:
              ansible_host: 192.168.2.12

# group_vars/backbone/p-nodes.yml - P router definitions
p:
  defaults:
    platform: ceos
    loopback_ipv4_pool: 10.255.0.0/27
    mpls_overlay_role: server
  nodes:
    - name: s1-p01
      id: 1
      mgmt_ip: 192.168.2.111/24
    - name: s2-p01
      id: 3
      mgmt_ip: 192.168.2.121/24

# group_vars/backbone/pe-nodes.yml - PE router definitions
pe:
  defaults:
    platform: ceos
    loopback_ipv4_pool: 10.255.1.0/27
    mpls_overlay_role: client
  nodes:
    - name: s1-pe01
      id: 1
      mgmt_ip: 192.168.2.11/24
    - name: s1-pe02
      id: 2
      mgmt_ip: 192.168.2.12/24

# group_vars/backbone/settings.yml - MPLS-specific settings
fabric_name: "backbone"
underlay_routing_protocol: "isis-sr"
overlay_routing_protocol: "ibgp"
bgp_as: "65000"

# Custom MPLS router configurations
custom_core_router_bgp:
  as_notation: "asdot"
  address_family_evpn:
    neighbor_default:
      encapsulation: "mpls"
      next_hop_self_source_interface: "Loopback0"

custom_core_router_isis:
  graceful_restart:
    enabled: True
  segment_routing_mpls:
    enabled: True
```

**Standard Node Types by Design:**

| Design Type | Standard Node Types | Description |
|-------------|---------------------|-------------|
| l3ls-evpn | spine, l3leaf, l2leaf, border_leaf, super_spine, overlay_controller | Traditional DC fabric with BGP EVPN |
| mpls | p, pe | Service provider core with MPLS |
| l2ls | l2spine, l2leaf | Layer 2 campus design |

**MPLS Node Type Requirements:**

- **NODE-001**: Application shall recognize "p" node type key in group_vars (provider router)
- **NODE-002**: Application shall recognize "pe" node type key in group_vars (provider edge router)
- **NODE-003**: Application shall extract device type from inventory.yml "vars: type: pe" pattern
- **NODE-004**: Application shall NOT require spine/leaf device types for MPLS design
- **NODE-005**: Application shall support custom_core_router_bgp and custom_core_router_isis variables
- **NODE-006**: Application shall handle ISIS-SR underlay and iBGP overlay routing protocols

#### Custom Node Type Definition

Users can define custom node types beyond the standard ones provided by each design:

```yaml
---
# group_vars/CUSTOM_FABRIC/custom_nodes.yml
# Define a custom "wan_edge" node type
wan_edge:
  defaults:
    platform: vEOS-lab
    bgp_as: 65100
    wan_role: edge
  nodes:
    - name: wan-edge-01
      id: 1
      mgmt_ip: 192.168.10.1/24
    - name: wan-edge-02
      id: 2
      mgmt_ip: 192.168.10.2/24

# Define a custom "core_router" node type
core_router:
  defaults:
    platform: 7280R3
    bgp_as: 65000
    routing_protocol: ospf
  node_groups:
    - group: CORE_PAIR
      nodes:
        - name: core-01
          id: 1
          mgmt_ip: 192.168.0.50/24
        - name: core-02
          id: 2
          mgmt_ip: 192.168.0.51/24
```

**Custom Node Type Requirements:**

- **CUSTOM-001**: Application shall discover any group_vars key with "defaults", "nodes", or "node_groups" as a potential node type
- **CUSTOM-002**: Custom node types shall be added to FabricDefinition.devices_by_type dictionary
- **CUSTOM-003**: Custom node types shall be accessible via get_devices_by_type(custom_type)
- **CUSTOM-004**: Documentation should recommend prefixing custom types to avoid conflicts (e.g., "org_wan_edge")

#### Jinja2 Template Variables Example

AVD inventories support Jinja2 template syntax for dynamic variable references:

```yaml
---
# group_vars/SPINES.yml - Using Jinja2 templates
l3spine:
  defaults:
    # Reference variable from hostvars
    platform: "{{ hostvars['spine01']['poc_platform'] }}"
    bgp_as: 65001
    # Use filter with default value
    mtu: "{{ mlag_peer_link_mtu | default(9214) }}"
  node_groups:
    - group: DC1_SPINES
      nodes:
        - name: spine01
          id: 1
          # Reference from host_vars
          mgmt_ip: "{{ hostvars['spine01'].ansible_host }}/24"

# group_vars/LEAVES/dot1x.yml - Complex Jinja2 example
radius_server:
  deadtime: 1
  hosts:
    - host: "{{ default_poc_radius_server }}"
      # Reference variable with fallback
      vrf: "{{ default_poc_radius_vrf }}"
      timeout: 100
      retransmit: 3
      key: "{{ default_poc_radius_key }}"

aaa_server_groups:
  - name: NAC
    type: "radius"
    servers:
      - server: "{{ default_poc_radius_server }}"
        vrf: "{{ default_poc_radius_vrf }}"

# group_vars/all.yml - Define variables referenced by templates
default_poc_radius_server: "10.0.0.100"
default_poc_radius_vrf: "MGMT"
default_poc_radius_key: "arista123"
mlag_peer_link_mtu: 9214

# host_vars/spine01.yml
ansible_host: 192.168.0.12
poc_platform: 7050X3
```

**Jinja2 Template Resolution Process:**

1. **Load Phase**: All YAML files are loaded with raw string values containing templates
2. **Context Building**: Create Jinja2 context from:
   - `global_vars` (from group_vars/all.yml)
   - `group_vars` (all group variables)
   - `host_vars` (all host variables)
   - `hostvars` (dictionary of all hosts with their variables)
3. **Template Resolution**: Recursively walk data structures and resolve `{{ ... }}` in strings
4. **Validation Phase**: Validate resolved values against schema

**Supported Jinja2 Features:**

| Feature | Syntax | Example |
|---------|--------|---------|
| Variable reference | `{{ variable }}` | `{{ default_mtu }}` |
| Dictionary access | `{{ dict['key'] }}` | `{{ hostvars['spine01']['platform'] }}` |
| Attribute access | `{{ obj.attribute }}` | `{{ hostvars.spine01.platform }}` |
| Filter with default | `{{ var \| default(value) }}` | `{{ mtu \| default(9214) }}` |
| String filters | `{{ var \| lower }}` | `{{ hostname \| upper }}` |
| Numeric filters | `{{ num \| int }}` | `{{ vlan_id \| int }}` |
| Chained filters | `{{ var \| lower \| replace('-', '_') }}` | `{{ name \| lower \| replace(' ', '-') }}` |

**Template Error Handling:**

```yaml
# ERROR: Undefined variable
platform: "{{ undefined_platform }}"
# Error message: "Variable 'undefined_platform' is undefined in group_vars/SPINES.yml"

# ERROR: Invalid syntax
platform: "{{ missing_closing_brace"
# Error message: "Template syntax error in group_vars/SPINES.yml: unclosed template"

# SUCCESS: Variable with default
platform: "{{ poc_platform | default('vEOS-lab') }}"
# Resolves to 'vEOS-lab' if poc_platform is not defined
```

### Validation Response Contract

```python
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    """Single validation issue."""

    severity: ValidationSeverity
    message: str
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    field_name: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Format validation issue for display."""
        parts = [f"[{self.severity.value.upper()}]"]

        if self.file_path:
            parts.append(f"{self.file_path}")
            if self.line_number:
                parts.append(f":{self.line_number}")

        parts.append(f"- {self.message}")

        if self.suggestion:
            parts.append(f"\n  Suggestion: {self.suggestion}")

        return " ".join(parts)

@dataclass
class ValidationResult:
    """Result of inventory validation."""

    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0

    def get_all_issues(self) -> List[ValidationIssue]:
        """Get all issues sorted by severity."""
        return self.errors + self.warnings + self.info
```

## 5. Acceptance Criteria

### Data Loading

- **AC-001**: Given valid inventory directory, When loading inventory, Then all YAML files are parsed successfully
- **AC-002**: Given YAML with syntax error, When loading inventory, Then ValidationIssue includes file path and line number
- **AC-003**: Given missing required directory, When loading inventory, Then clear error message indicates which directory is missing
- **AC-004**: Given host_vars without group_vars, When loading inventory, Then loading succeeds with only host-level data
- **AC-005**: Given group_vars/GROUP as directory, When loading, Then all .yml and .yaml files in directory are loaded and merged
- **AC-006**: Given group_vars/GROUP as file, When loading, Then single file is loaded
- **AC-007**: Given group_vars with mixed file and directory entries, When loading, Then both formats are processed correctly
- **AC-008**: Given directory with multiple YAML files, When loading, Then files are processed in alphabetical order
- **AC-009**: Given directory with duplicate keys across files, When loading, Then later files override earlier files
- **AC-010**: Given host_vars/HOST as directory, When loading, Then all YAML files in directory are loaded and merged

### Data Validation

- **AC-011**: Given device missing required field, When validating, Then ValidationIssue indicates which field is missing
- **AC-012**: Given invalid IP address format, When validating, Then ValidationIssue explains IP format requirements
- **AC-013**: Given duplicate hostname, When validating, Then ValidationIssue lists all duplicate hostnames
- **AC-014**: Given unsupported platform, When validating, Then ValidationIssue lists supported platforms

### Type Safety

- **AC-015**: Given inventory data, When accessing fields, Then type checker validates field access
- **AC-016**: Given optional field, When accessing, Then code handles None case explicitly
- **AC-017**: Given IP address field, When assigning value, Then only IPv4Address or IPv6Address accepted

### Error Messages

- **AC-018**: Given validation error, When displaying to user, Then message includes actionable suggestion
- **AC-019**: Given file parsing error, When reporting, Then message shows file path and syntax error location
- **AC-020**: Given schema violation, When reporting, Then message explains expected vs actual structure

### Schema Integration

- **AC-021**: Given py-avd library available, When loading platforms, Then platforms are loaded from pyavd._eos_designs.schema
- **AC-022**: Given py-avd library unavailable, When loading platforms, Then fallback list is used without error
- **AC-023**: Given schema constants loaded once, When accessing again, Then cached values are returned
- **AC-024**: Given unsupported platform, When validating device, Then error message lists all supported platforms from schema

### Device Type Mapping

- **AC-025**: Given device with type l3spine, When parsing, Then device type is mapped to spine
- **AC-026**: Given device with type l2leaf, When parsing, Then device type is mapped to leaf
- **AC-027**: Given device with type l3leaf, When parsing, Then device type is mapped to leaf
- **AC-028**: Given device with canonical type spine, When parsing, Then device type remains spine
- **AC-029**: Given device with unknown type and permissive mode, When parsing, Then device is accepted with warning
- **AC-030**: Given device with unknown type and strict mode, When parsing, Then validation error is raised

### Custom Structured Configuration

- **AC-031**: Given custom_structured_platform_settings in group_vars, When loading, Then platform settings are loaded
- **AC-032**: Given device matches platform in custom settings, When applying, Then custom settings are merged with device
- **AC-033**: Given custom_structured_configuration in group_vars, When loading, Then custom config is loaded
- **AC-034**: Given custom config and device config, When merging, Then custom config overrides device config
- **AC-035**: Given nested custom config, When merging, Then deep merge is performed correctly

### Jinja2 Template Variables

- **AC-036**: Given YAML value `{{ variable }}`, When resolving templates, Then variable is replaced with value from context
- **AC-037**: Given `{{ hostvars['hostname']['key'] }}`, When resolving, Then value from host_vars/hostname.yml is used
- **AC-038**: Given `{{ var | default(123) }}`, When var is undefined, Then default value 123 is used
- **AC-039**: Given `{{ var | default(123) }}`, When var is defined, Then var value is used (default ignored)
- **AC-040**: Given undefined variable without default, When resolving, Then clear error with variable name is raised
- **AC-041**: Given template in nested structure, When resolving, Then all nested templates are resolved
- **AC-042**: Given non-string value (int, bool, list), When resolving, Then value is preserved unchanged
- **AC-043**: Given template syntax error, When resolving, Then error includes file path and line information
- **AC-044**: Given resolved template produces invalid type, When validating, Then type validation error is raised
- **AC-045**: Given multiple templates in same string, When resolving, Then all templates are resolved correctly

### MPLS Design Type Support

- **AC-046**: Given MPLS inventory with "p:" node type key, When loading, Then P routers are discovered and loaded
- **AC-047**: Given MPLS inventory with "pe:" node type key, When loading, Then PE routers are discovered and loaded
- **AC-048**: Given inventory with vars: type: "pe", When parsing hosts, Then device_type is set to "pe"
- **AC-049**: Given MPLS design fabric, When validating, Then no error for missing spine devices
- **AC-050**: Given MPLS fabric with P and PE devices, When retrieving all devices, Then both types are returned
- **AC-051**: Given custom_core_router_bgp in group_vars, When loading, Then custom BGP config is preserved
- **AC-052**: Given custom_core_router_isis in group_vars, When loading, Then custom ISIS config is preserved
- **AC-053**: Given FabricDefinition with devices_by_type, When accessing spine_devices property, Then empty list returned if no spine type
- **AC-054**: Given FabricDefinition with devices_by_type: {"p": [...], "pe": [...]}, When calling get_devices_by_type("p"), Then P routers returned
- **AC-055**: Given MPLS inventory (examples/eos-design-mpls), When loading complete inventory, Then all P and PE devices loaded correctly

### Multi-Design-Type Flexibility

- **AC-056**: Given inventory with custom node type "wan_edge:", When loading, Then devices are discovered with type "wan_edge"
- **AC-057**: Given FabricDefinition without spine devices, When validating with skip_topology_validation=True, Then no validation errors
- **AC-058**: Given inventory with mixed designs (l3ls-evpn and mpls), When loading, Then both fabrics loaded with correct types
- **AC-059**: Given node type not in DEVICE_TYPE_MAPPING, When loading with permissive mode, Then device loaded with warning
- **AC-060**: Given node type not in DEVICE_TYPE_MAPPING, When loading with strict mode, Then validation error raised

### Custom Node Types

- **AC-061**: Given group_vars with "wan_edge:" key containing "defaults" and "nodes", When discovering node types, Then "wan_edge" is identified as node type
- **AC-062**: Given custom node type "core_router:" with devices, When loading inventory, Then devices are added to fabric.devices_by_type["core_router"]
- **AC-063**: Given FabricDefinition with custom node type "wan_edge", When calling get_devices_by_type("wan_edge"), Then custom devices returned
- **AC-064**: Given inventory with both standard (spine) and custom (wan_edge) node types, When loading, Then both types discovered and loaded
- **AC-065**: Given custom node type with node_groups structure, When parsing, Then all nodes in all groups are discovered
- **AC-066**: Given l3ls-evpn design with custom "dmz_leaf" node type, When loading, Then standard types (spine, l3leaf) and custom type (dmz_leaf) coexist

## 6. Test Automation Strategy

### Unit Tests

```python
def test_device_definition_validation():
    """Test device definition validation rules."""

    # Valid device
    device = DeviceDefinition(
        hostname="spine1",
        platform="vEOS-lab",
        mgmt_ip=IPv4Address("192.168.0.10"),
        device_type="spine",
        fabric="DC1"
    )
    assert device.hostname == "spine1"

    # Invalid hostname
    with pytest.raises(ValueError, match="Invalid hostname"):
        DeviceDefinition(
            hostname="spine#1",  # Invalid character
            platform="vEOS-lab",
            mgmt_ip=IPv4Address("192.168.0.10"),
            device_type="spine",
            fabric="DC1"
        )

def test_inventory_duplicate_detection():
    """Test duplicate hostname detection."""
    inventory = InventoryData(root_path=Path("."))

    fabric = FabricDefinition(name="DC1", design_type="l3ls-evpn")
    fabric.spine_devices = [
        DeviceDefinition(
            hostname="spine1",
            platform="vEOS-lab",
            mgmt_ip=IPv4Address("192.168.0.10"),
            device_type="spine",
            fabric="DC1"
        ),
        DeviceDefinition(
            hostname="spine1",  # Duplicate
            platform="vEOS-lab",
            mgmt_ip=IPv4Address("192.168.0.11"),
            device_type="spine",
            fabric="DC1"
        )
    ]

    inventory.fabrics.append(fabric)
    errors = inventory.validate()

    assert len(errors) > 0
    assert "Duplicate hostnames" in errors[0]
```

### Schema Utility Tests

```python
import pytest
from unittest.mock import Mock, patch
from avd_cli.utils.schema import (
    get_supported_platforms,
    get_supported_device_types,
    get_avd_schema_version,
    clear_schema_cache,
)

def test_get_platforms_from_pyavd():
    """Test loading platforms from py-avd."""
    with patch('avd_cli.utils.schema.AvdSchema') as mock_schema:
        mock_schema.return_value.get_platforms.return_value = [
            "vEOS-lab", "7280R3"
        ]

        clear_schema_cache()  # Clear any cached values
        platforms = get_supported_platforms()

        assert "vEOS-lab" in platforms
        assert "7280R3" in platforms

def test_get_platforms_fallback():
    """Test fallback when py-avd unavailable."""
    with patch('avd_cli.utils.schema.AvdSchema', side_effect=ImportError):
        clear_schema_cache()
        platforms = get_supported_platforms()

        # Should use fallback list
        assert "vEOS-lab" in platforms
        assert isinstance(platforms, list)

def test_platform_caching():
    """Test that platforms are cached after first load."""
    with patch('avd_cli.utils.schema.AvdSchema') as mock_schema:
        mock_schema.return_value.get_platforms.return_value = ["vEOS-lab"]

        clear_schema_cache()
        platforms1 = get_supported_platforms()
        platforms2 = get_supported_platforms()

        # Should only call schema once due to caching
        assert mock_schema.call_count == 1
        assert platforms1 is platforms2
```

### Directory Loading Tests

```python
import pytest
from pathlib import Path
from avd_cli.logics.loader import InventoryLoader

def test_load_group_vars_from_directory(tmp_path):
    """Test loading group_vars from directory with multiple files."""
    # Create directory structure
    group_vars_dir = tmp_path / "inventory" / "group_vars" / "atd"
    group_vars_dir.mkdir(parents=True)

    # Create multiple YAML files
    (group_vars_dir / "basics.yml").write_text("""
hostname: '{{ inventory_hostname }}'
timezone: Europe/Paris
""")

    (group_vars_dir / "aaa.yml").write_text("""
local_users:
  - name: admin
    role: network-admin
""")

    (group_vars_dir / "platform.yml").write_text("""
platform: vEOS-lab
timezone: UTC  # Override from basics.yml
""")

    loader = InventoryLoader()
    group_vars = loader._load_group_vars(tmp_path / "inventory")

    # All files should be loaded
    assert "hostname" in group_vars["atd"]
    assert "local_users" in group_vars["atd"]
    assert "platform" in group_vars["atd"]

    # Later file (platform.yml) should override earlier (basics.yml)
    assert group_vars["atd"]["timezone"] == "UTC"

def test_load_mixed_file_and_directory_format(tmp_path):
    """Test loading group_vars with mixed file and directory formats."""
    group_vars_path = tmp_path / "inventory" / "group_vars"
    group_vars_path.mkdir(parents=True)

    # Create directory with multiple files
    (group_vars_path / "all").mkdir()
    (group_vars_path / "all" / "basics.yml").write_text("var1: value1")
    (group_vars_path / "all" / "extras.yml").write_text("var2: value2")

    # Create single file
    (group_vars_path / "FABRIC.yml").write_text("fabric_name: DC1")

    loader = InventoryLoader()
    group_vars = loader._load_group_vars(tmp_path / "inventory")

    # Both formats should be loaded
    assert "all" in group_vars
    assert group_vars["all"]["var1"] == "value1"
    assert group_vars["all"]["var2"] == "value2"

    assert "FABRIC" in group_vars
    assert group_vars["FABRIC"]["fabric_name"] == "DC1"

def test_deep_merge_nested_dicts(tmp_path):
    """Test deep merge of nested dictionaries from multiple files."""
    group_vars_dir = tmp_path / "inventory" / "group_vars" / "test"
    group_vars_dir.mkdir(parents=True)

    # File 1: Base configuration
    (group_vars_dir / "base.yml").write_text("""
router_bgp:
  as: 65001
  neighbors:
    - ip: 10.0.0.1
      remote_as: 65002
""")

    # File 2: Override and extend
    (group_vars_dir / "override.yml").write_text("""
router_bgp:
  as: 65001  # Same value
  router_id: 1.1.1.1  # New key
  neighbors:  # This will override the entire list
    - ip: 10.0.0.2
      remote_as: 65003
""")

    loader = InventoryLoader()
    group_vars = loader._load_group_vars(tmp_path / "inventory")

    # Later file should override nested values
    assert group_vars["test"]["router_bgp"]["as"] == 65001
    assert group_vars["test"]["router_bgp"]["router_id"] == "1.1.1.1"
    # Note: Lists are replaced, not merged
    assert len(group_vars["test"]["router_bgp"]["neighbors"]) == 1
    assert group_vars["test"]["router_bgp"]["neighbors"][0]["ip"] == "10.0.0.2"

def test_alphabetical_file_order(tmp_path):
    """Test that files are processed in alphabetical order."""
    group_vars_dir = tmp_path / "inventory" / "group_vars" / "test"
    group_vars_dir.mkdir(parents=True)

    # Create files with specific names to test order
    (group_vars_dir / "c_third.yml").write_text("order: third")
    (group_vars_dir / "a_first.yml").write_text("order: first")
    (group_vars_dir / "b_second.yml").write_text("order: second")

    loader = InventoryLoader()
    group_vars = loader._load_group_vars(tmp_path / "inventory")

    # Last alphabetical file wins
    assert group_vars["test"]["order"] == "third"

def test_host_vars_directory_support(tmp_path):
    """Test loading host_vars from directories."""
    host_vars_dir = tmp_path / "inventory" / "host_vars" / "spine1"
    host_vars_dir.mkdir(parents=True)

    (host_vars_dir / "system.yml").write_text("hostname: spine1")
    (host_vars_dir / "interfaces.yml").write_text("""
interfaces:
  Ethernet1:
    description: uplink
""")

    loader = InventoryLoader()
    host_vars = loader._load_host_vars(tmp_path / "inventory")

    assert "spine1" in host_vars
    assert host_vars["spine1"]["hostname"] == "spine1"
    assert "interfaces" in host_vars["spine1"]
```

### Device Type Mapping Tests

```python
import pytest
from avd_cli.logics.loader import InventoryLoader
from avd_cli.models.inventory import DeviceDefinition

def test_l3spine_maps_to_spine():
    """Test that l3spine device type maps to canonical spine."""
    loader = InventoryLoader()

    # Simulate device data with l3spine type
    node_data = {
        "name": "spine01",
        "mgmt_ip": "192.168.0.10",
        "platform": "7050X3",
    }

    device = loader._parse_device_node(
        node_data, device_type="l3spine", fabric_name="DC1", host_vars={}
    )

    assert device is not None
    assert device.device_type == "spine"  # Mapped to canonical type
    assert device.hostname == "spine01"

def test_l2leaf_maps_to_leaf():
    """Test that l2leaf device type maps to canonical leaf."""
    loader = InventoryLoader()

    node_data = {
        "name": "leaf01",
        "mgmt_ip": "192.168.0.20",
        "platform": "722XP",
    }

    device = loader._parse_device_node(
        node_data, device_type="l2leaf", fabric_name="DC1", host_vars={}
    )

    assert device is not None
    assert device.device_type == "leaf"  # Mapped to canonical type

def test_canonical_types_remain_unchanged():
    """Test that canonical types are not remapped."""
    loader = InventoryLoader()

    node_data = {
        "name": "spine01",
        "mgmt_ip": "192.168.0.10",
        "platform": "vEOS-lab",
    }

    device = loader._parse_device_node(
        node_data, device_type="spine", fabric_name="DC1", host_vars={}
    )

    assert device is not None
    assert device.device_type == "spine"  # Remains canonical
```

### Custom Structured Configuration Tests

```python
def test_custom_platform_settings_loaded():
    """Test loading custom_structured_platform_settings."""
    loader = InventoryLoader()

    group_vars = {
        "FABRIC": {
            "custom_structured_platform_settings": [
                {
                    "platforms": ["7050X3"],
                    "management_interface": "Management1",
                    "default_interface_mtu": 9214,
                }
            ]
        }
    }

    # Verify settings are loaded
    settings = group_vars["FABRIC"]["custom_structured_platform_settings"]
    assert len(settings) == 1
    assert "7050X3" in settings[0]["platforms"]
    assert settings[0]["management_interface"] == "Management1"

def test_custom_config_merges_with_device():
    """Test that custom_structured_configuration merges with device config."""
    from avd_cli.logics.loader import InventoryLoader

    loader = InventoryLoader()

    base_config = {
        "router_bgp": {
            "as": 65001,
        }
    }

    custom_config = {
        "router_bgp": {
            "router_id": "1.1.1.1",
        },
        "logging": {
            "console": "informational",
        },
    }

    merged = loader._deep_merge(base_config, custom_config)

    # BGP AS should remain, router_id added
    assert merged["router_bgp"]["as"] == 65001
    assert merged["router_bgp"]["router_id"] == "1.1.1.1"

    # Logging added
    assert merged["logging"]["console"] == "informational"
```

### Jinja2 Template Resolution Tests

```python
def test_simple_variable_resolution():
    """Test resolving simple Jinja2 variable references."""
    from avd_cli.logics.templating import TemplateResolver

    context = {
        "default_mtu": 9214,
        "fabric_name": "DC1",
    }

    resolver = TemplateResolver(context)

    # Resolve simple variable
    result = resolver.resolve("{{ default_mtu }}")
    assert result == "9214"  # Note: templates resolve to strings by default

    # Resolve string variable
    result = resolver.resolve("{{ fabric_name }}")
    assert result == "DC1"

def test_hostvars_dictionary_access():
    """Test accessing hostvars with dictionary syntax."""
    from avd_cli.logics.templating import TemplateResolver

    context = {
        "hostvars": {
            "spine01": {
                "poc_platform": "7050X3",
                "ansible_host": "192.168.0.12",
            },
            "leaf01": {
                "poc_platform": "722XP",
            }
        }
    }

    resolver = TemplateResolver(context)

    # Test hostvars access
    result = resolver.resolve("{{ hostvars['spine01']['poc_platform'] }}")
    assert result == "7050X3"

    # Test nested hostvars access
    result = resolver.resolve("{{ hostvars['spine01']['ansible_host'] }}")
    assert result == "192.168.0.12"

def test_default_filter():
    """Test Jinja2 default filter."""
    from avd_cli.logics.templating import TemplateResolver

    context = {
        "defined_var": "value",
    }

    resolver = TemplateResolver(context)

    # Variable exists - use it
    result = resolver.resolve("{{ defined_var | default('fallback') }}")
    assert result == "value"

    # Variable doesn't exist - use default
    result = resolver.resolve("{{ undefined_var | default('fallback') }}")
    assert result == "fallback"

    # Numeric default
    result = resolver.resolve("{{ undefined_mtu | default(9214) }}")
    assert result == "9214"

def test_string_filters():
    """Test common Jinja2 string filters."""
    from avd_cli.logics.templating import TemplateResolver

    context = {
        "hostname": "SPINE-01",
        "interface": "ethernet1",
    }

    resolver = TemplateResolver(context)

    # Lower filter
    result = resolver.resolve("{{ hostname | lower }}")
    assert result == "spine-01"

    # Upper filter
    result = resolver.resolve("{{ interface | upper }}")
    assert result == "ETHERNET1"

    # Replace filter
    result = resolver.resolve("{{ hostname | replace('-', '_') }}")
    assert result == "SPINE_01"

def test_recursive_template_resolution():
    """Test resolving templates in nested data structures."""
    from avd_cli.logics.templating import TemplateResolver

    context = {
        "radius_server": "10.0.0.100",
        "radius_vrf": "MGMT",
        "mtu": 9214,
    }

    data = {
        "aaa": {
            "servers": [
                {
                    "host": "{{ radius_server }}",
                    "vrf": "{{ radius_vrf }}",
                }
            ],
        },
        "interfaces": {
            "Ethernet1": {
                "mtu": "{{ mtu }}",
            }
        }
    }

    resolver = TemplateResolver(context)
    resolved = resolver.resolve_dict(data)

    # Check nested resolution
    assert resolved["aaa"]["servers"][0]["host"] == "10.0.0.100"
    assert resolved["aaa"]["servers"][0]["vrf"] == "MGMT"
    assert resolved["interfaces"]["Ethernet1"]["mtu"] == "9214"

def test_undefined_variable_error():
    """Test error handling for undefined variables."""
    from avd_cli.logics.templating import TemplateResolver, TemplateError

    context = {}
    resolver = TemplateResolver(context)

    # Should raise clear error
    with pytest.raises(TemplateError, match="undefined_variable"):
        resolver.resolve("{{ undefined_variable }}")

def test_template_syntax_error():
    """Test error handling for malformed templates."""
    from avd_cli.logics.templating import TemplateResolver, TemplateError

    context = {}
    resolver = TemplateResolver(context)

    # Unclosed template
    with pytest.raises(TemplateError, match="syntax"):
        resolver.resolve("{{ unclosed")

    # Invalid syntax
    with pytest.raises(TemplateError):
        resolver.resolve("{{ 'invalid syntax ]}")

def test_preserve_non_template_strings():
    """Test that non-template strings are preserved unchanged."""
    from avd_cli.logics.templating import TemplateResolver

    context = {}
    resolver = TemplateResolver(context)

    # Regular strings should pass through
    assert resolver.resolve("regular string") == "regular string"
    assert resolver.resolve("has {{ but no closing") == "has {{ but no closing"
    assert resolver.resolve("10.0.0.1") == "10.0.0.1"

def test_preserve_non_string_types():
    """Test that non-string types are preserved during resolution."""
    from avd_cli.logics.templating import TemplateResolver

    context = {}

    data = {
        "integer": 123,
        "boolean": True,
        "list": [1, 2, 3],
        "null": None,
    }

    resolver = TemplateResolver(context)
    resolved = resolver.resolve_dict(data)

    # Types should be preserved
    assert resolved["integer"] == 123
    assert resolved["boolean"] is True
    assert resolved["list"] == [1, 2, 3]
    assert resolved["null"] is None
```

### Integration Tests

- Test loading real AVD inventory samples (e.g., examples/atd-inventory)
- Verify py-avd compatibility with loaded data
- Test large inventory performance (<2s validation)
- Test malformed YAML error handling
- Test schema constant loading with real py-avd library
- Test directory-based group_vars and host_vars with real AVD structures
- Test mixed file/directory formats in production inventories
- Test device type mapping with real AVD inventories using l3spine/l2leaf
- Test custom_structured_platform_settings with multiple platforms
- Test custom_structured_configuration merge behavior

### MPLS Design Integration Tests

```python
def test_load_mpls_inventory():
    """Test loading MPLS design inventory (examples/eos-design-mpls)."""
    from avd_cli.logics.loader import InventoryLoader

    loader = InventoryLoader()
    inventory = loader.load(Path("examples/eos-design-mpls"))

    # Verify backbone fabric loaded
    assert len(inventory.fabrics) == 1
    fabric = inventory.fabrics[0]
    assert fabric.name == "backbone"
    assert fabric.design_type == "mpls"  # Detected from settings or default

    # Verify P routers discovered
    p_routers = fabric.get_devices_by_type("p")
    assert len(p_routers) == 4  # s1-p01, s1-p02, s2-p01, s2-p02
    assert all(d.device_type == "p" for d in p_routers)

    # Verify PE routers discovered
    pe_routers = fabric.get_devices_by_type("pe")
    assert len(pe_routers) == 5  # s1-pe01, s1-pe02, s1-pe03, s1-pe04, s2-pe01
    assert all(d.device_type == "pe" for d in pe_routers)

    # Verify custom MPLS settings loaded
    assert "custom_core_router_bgp" in inventory.group_vars.get("backbone", {})
    assert "custom_core_router_isis" in inventory.group_vars.get("backbone", {})

    # Verify no spine devices (MPLS doesn't use spine/leaf)
    assert len(fabric.spine_devices) == 0
    assert len(fabric.leaf_devices) == 0

def test_mpls_device_discovery_from_vars_type():
    """Test discovering device type from inventory.yml vars: type: 'pe' pattern."""
    from avd_cli.logics.loader import InventoryLoader

    loader = InventoryLoader()
    inventory = loader.load(Path("examples/eos-design-mpls"))

    # Find a PE device
    pe_device = inventory.get_device_by_hostname("s1-pe01")
    assert pe_device is not None
    assert pe_device.device_type == "pe"

    # Find a P device
    p_device = inventory.get_device_by_hostname("s1-p01")
    assert p_device is not None
    assert p_device.device_type == "p"

def test_mpls_custom_router_configs():
    """Test that custom_core_router_bgp and custom_core_router_isis are loaded."""
    from avd_cli.logics.loader import InventoryLoader

    loader = InventoryLoader()
    inventory = loader.load(Path("examples/eos-design-mpls"))

    backbone_vars = inventory.group_vars.get("backbone", {})

    # Verify custom BGP config
    assert "custom_core_router_bgp" in backbone_vars
    bgp_config = backbone_vars["custom_core_router_bgp"]
    assert bgp_config["as_notation"] == "asdot"
    assert "address_family_evpn" in bgp_config

    # Verify custom ISIS config
    assert "custom_core_router_isis" in backbone_vars
    isis_config = backbone_vars["custom_core_router_isis"]
    assert isis_config["graceful_restart"]["enabled"] is True
    assert isis_config["segment_routing_mpls"]["enabled"] is True

def test_fabric_with_custom_node_types():
    """Test FabricDefinition with custom node types (p, pe)."""
    from avd_cli.models.inventory import FabricDefinition, DeviceDefinition
    from ipaddress import ip_address

    # Create fabric with custom MPLS node types
    fabric = FabricDefinition(
        name="backbone",
        design_type="mpls",
        devices_by_type={
            "p": [
                DeviceDefinition(
                    hostname="s1-p01",
                    platform="ceos",
                    mgmt_ip=ip_address("192.168.2.111"),
                    device_type="p",
                    fabric="backbone"
                )
            ],
            "pe": [
                DeviceDefinition(
                    hostname="s1-pe01",
                    platform="ceos",
                    mgmt_ip=ip_address("192.168.2.11"),
                    device_type="pe",
                    fabric="backbone"
                )
            ]
        }
    )

    # Verify devices retrieved by type
    assert len(fabric.get_devices_by_type("p")) == 1
    assert len(fabric.get_devices_by_type("pe")) == 1
    assert len(fabric.get_all_devices()) == 2

    # Verify backward compatibility properties return empty
    assert len(fabric.spine_devices) == 0
    assert len(fabric.leaf_devices) == 0

def test_mpls_validation_no_spine_required():
    """Test that MPLS fabric validation doesn't require spine devices."""
    from avd_cli.models.inventory import InventoryData, FabricDefinition, DeviceDefinition
    from ipaddress import ip_address
    from pathlib import Path

    fabric = FabricDefinition(
        name="backbone",
        design_type="mpls",
        devices_by_type={
            "p": [
                DeviceDefinition(
                    hostname="s1-p01",
                    platform="ceos",
                    mgmt_ip=ip_address("192.168.2.111"),
                    device_type="p",
                    fabric="backbone"
                )
            ]
        }
    )

    inventory = InventoryData(
        root_path=Path("."),
        fabrics=[fabric]
    )

    # Validate with topology validation enabled
    errors = inventory.validate(skip_topology_validation=False)
    
    # Should NOT error about missing spines for MPLS design
    assert not any("spine devices" in err for err in errors)
    assert len(errors) == 0
```

## 7. Rationale & Context

### Why Dataclasses over Dictionaries?

Using typed dataclasses provides:

- **Type Safety**: Mypy catches field access errors at development time
- **IDE Support**: Autocomplete for field names and types
- **Validation**: Post-init validation ensures data integrity
- **Documentation**: Types serve as inline documentation
- **Refactoring**: Safe field renames across codebase

### Why Explicit Validation?

Validating data at load time prevents:

- **Late Failures**: Catch errors before expensive processing
- **Unclear Errors**: Validation provides specific, actionable messages
- **Partial Failures**: Stop before generating invalid configs
- **Debugging Pain**: Clear errors reduce troubleshooting time

### Why ipaddress Module?

Python's ipaddress module provides:

- **Validation**: Automatic IP address format validation
- **Type Safety**: Distinct types for IPv4 vs IPv6
- **Operations**: Network calculations, subnet checks
- **Standards**: Follows RFC specifications

### Why Support Directory-Based Variables?

Supporting directories for group_vars and host_vars provides:

- **Modularity**: Large variable sets can be split into focused, manageable files
- **Organization**: Related variables grouped by concern (aaa.yml, ntp.yml, platform.yml)
- **Collaboration**: Multiple team members can work on different files without merge conflicts
- **Maintainability**: Easier to locate and update specific configuration sections
- **Scalability**: Complex inventories remain readable and navigable
- **Ansible Compatibility**: Follows standard Ansible inventory conventions

Real-world example from ATD inventory:

```text
group_vars/atd/
  ├── aaa.yml        # AAA configuration (local users, TACACS)
  ├── alias.yml      # Command aliases
  ├── basics.yml     # Hostname, spanning tree, routing
  ├── cv_server.yml  # CloudVision configuration
  ├── defaults.yml   # Default variables
  ├── platform.yml   # Platform-specific settings
  ├── sflow.yml      # sFlow configuration
  └── snmp.yml       # SNMP configuration
```

This structure allows:

- Security team to manage aaa.yml independently
- Network team to update routing in basics.yml
- Monitoring team to configure snmp.yml and sflow.yml
- All changes merge cleanly without conflicts

### Why Support Device Type Mapping?

AVD uses descriptive device type names that map to functional roles:

- **Backward Compatibility**: Existing AVD inventories use l3spine, l2leaf terminology
- **Clarity**: l3spine and l2leaf are more descriptive than generic spine/leaf
- **Flexibility**: Allows both AVD-specific and canonical types in same inventory
- **Migration**: Enables gradual migration from legacy type names to canonical ones
- **Extensibility**: Foundation for supporting custom device types in future

**Type Mapping Benefits:**

- Users can continue using familiar AVD terminology
- Internal processing uses consistent canonical types
- Validation can work with both naming conventions
- Error messages reference correct type names per context

### Why Support Custom Structured Configuration?

Custom structured configuration is essential for real-world AVD deployments:

- **Schema Extension**: Allows adding platform-specific features not in base AVD schema
- **Platform Diversity**: Different hardware platforms require different configurations (PoE, storm control, MTU)
- **Feature Support**: Enable/disable features per platform (queue monitoring, BGP wait-for-convergence)
- **Operational Requirements**: Organization-specific settings that extend base AVD (custom VLANs, logging, monitoring)
- **AVD Compatibility**: Follows official AVD pattern for schema customization

**Real-World Use Cases:**

```yaml
# Example: Campus switches need PoE, access switches don't
custom_structured_platform_settings:
  - platforms: [722XP, 720XP]  # Campus switches
    feature_support:
      poe: true
      interface_storm_control: true
  - platforms: [7050X3]  # Data center switches
    feature_support:
      poe: false
      queue_monitor_length_notify: false
```

This pattern is documented in the [AVD Custom Structured Configuration Guide](https://avd.arista.com/devel/ansible_collections/arista/avd/roles/eos_designs/docs/how-to/custom-structured-configuration.html) and is widely used in production AVD deployments.

### Why Support Multiple AVD Design Types?

AVD supports multiple network design patterns, each with different topology structures:

- **L3LS-EVPN Design**: Traditional data center with spine/leaf architecture
- **MPLS Design**: Service provider core with P (provider) and PE (provider edge) routers
- **L2LS Design**: Layer 2 spine/leaf for campus or small deployments

**Why Flexible Node Type Support is Essential:**

1. **Design Diversity**: Different designs use different device roles (p/pe vs spine/leaf vs l2spine/l2leaf)
2. **User Inventories**: Users define custom node types via custom_node_type_keys and node_type_keys
3. **No Forced Classification**: Attempting to map all types to spine/leaf breaks MPLS and custom designs
4. **AVD Compatibility**: py-avd supports flexible node types, avd-cli must match this flexibility

**MPLS Design Characteristics:**

```yaml
# MPLS uses P and PE routers, NOT spine/leaf
p:  # Provider routers (core)
  defaults:
    platform: ceos
    mpls_overlay_role: server
  nodes:
    - name: s1-p01
      id: 1

pe:  # Provider edge routers (customer-facing)
  defaults:
    platform: ceos
    mpls_overlay_role: client
    evpn_role: client
  nodes:
    - name: s1-pe01
      id: 1

# Routing protocols differ from L3LS-EVPN
underlay_routing_protocol: "isis-sr"  # Not BGP
overlay_routing_protocol: "ibgp"       # Not eBGP EVPN
```

**Design-Agnostic Implementation Approach:**

- Use `devices_by_type: Dict[str, List[DeviceDefinition]]` instead of hardcoded spine_devices/leaf_devices
- Discover node type keys dynamically from group_vars (look for "p:", "pe:", "spine:", "leaf:", etc.)
- Extract device type from inventory.yml vars (e.g., `vars: type: "pe"`)
- Don't validate topology structure unless design_type is known and requires it
- Support backward compatibility via @property accessors (spine_devices, leaf_devices)

**Benefits:**

- ✅ examples/eos-design-mpls works without modification
- ✅ examples/eos-design-complex continues to work (L3LS-EVPN)
- ✅ Custom node types in user inventories are supported
- ✅ Future AVD designs automatically supported
- ✅ Matches py-avd's flexible design philosophy

### Why Support Jinja2 Templates?

Jinja2 template support is essential for AVD inventory compatibility and DRY principles:

- **Ansible Compatibility**: AVD inventories are Ansible-based and extensively use Jinja2 templates
- **DRY Principle**: Variables can reference other variables, avoiding duplication
- **Dynamic Configuration**: Platform-specific values can be computed from host variables
- **Maintainability**: Centralize common values and reference them throughout inventory
- **Flexibility**: Support conditional logic and filters for complex scenarios

**Real-World Use Cases:**

```yaml
# Reference platform from host_vars
platform: "{{ hostvars['spine01']['poc_platform'] }}"  # Avoids hardcoding

# Default values reduce boilerplate
mtu: "{{ mlag_peer_link_mtu | default(9214) }}"  # Default if not specified

# Consistent naming from variables
server: "{{ default_poc_radius_server }}"  # Single source of truth
vrf: "{{ default_poc_radius_vrf }}"        # Easy to update globally
```

**Template Processing Flow:**

1. **Load YAML**: Parse all YAML files with template strings intact
2. **Build Context**: Aggregate all variables (global, group, host, hostvars)
3. **Resolve Templates**: Walk data structures recursively, resolve `{{ ... }}` in strings
4. **Validate**: Perform schema validation on resolved values
5. **Process**: Continue with fully resolved data

This approach matches Ansible's variable resolution behavior and ensures AVD inventories can be processed standalone without requiring full Ansible runtime.

## 8. Dependencies & External Integrations

### External Systems

- **EXT-001**: File System - Read access to inventory YAML files

### Data Dependencies

- **DAT-001**: AVD Schema - Implicit schema from py-avd library
- **DAT-002**: Ansible Inventory - Follows Ansible conventions for group_vars/host_vars

### Technology Platform Dependencies

- **PLT-001**: Python 3.9+ - dataclasses, type hints, ipaddress module
- **PLT-002**: PyYAML - YAML parsing library
- **PLT-003**: Jinja2 >=3.0 - Template engine for variable resolution
- **PLT-004**: pydantic (optional) - Enhanced data validation
- **PLT-005**: py-avd (pyavd) - Core AVD library providing schema definitions and constants

## 9. Examples & Edge Cases

### Dynamic Node Type Discovery

The inventory loader shall dynamically discover node type keys from group_vars without hardcoded assumptions:

```python
def _discover_node_type_keys(self, group_vars: Dict[str, Dict[str, Any]]) -> Set[str]:
    """Discover all node type keys defined in group_vars.
    
    Scans group_vars for keys that look like AVD node type definitions.
    These typically have "defaults" and "nodes" or "node_groups" sub-keys.
    
    Examples of node type keys:
    - Standard L3LS-EVPN: "spine", "l3spine", "leaf", "l3leaf", "l2leaf"
    - MPLS: "p", "pe"
    - Custom: "wan_edge", "core_router", etc.
    
    Parameters
    ----------
    group_vars : Dict[str, Dict[str, Any]]
        All group variables
    
    Returns
    -------
    Set[str]
        Set of discovered node type keys
    """
    node_type_keys = set()
    
    for group_name, group_data in group_vars.items():
        if not isinstance(group_data, dict):
            continue
            
        # Check each key in group_data
        for key, value in group_data.items():
            if not isinstance(value, dict):
                continue
            
            # Heuristic: node type keys have "defaults", "nodes", or "node_groups"
            has_defaults = "defaults" in value
            has_nodes = "nodes" in value
            has_node_groups = "node_groups" in value
            
            if has_defaults or has_nodes or has_node_groups:
                self.logger.debug("Discovered node type key: %s (in group %s)", key, group_name)
                node_type_keys.add(key)
    
    return node_type_keys

# Usage in _parse_fabrics:
def _parse_fabrics(
    self,
    global_vars: Dict[str, Any],
    group_vars: Dict[str, Dict[str, Any]],
    host_vars: Dict[str, Dict[str, Any]],
    group_hierarchy: Dict[str, List[str]],
    host_to_group: Dict[str, str],
) -> List[FabricDefinition]:
    """Parse loaded YAML data into fabric and device structures."""
    fabrics: List[FabricDefinition] = []
    devices_by_fabric: Dict[str, Dict[str, List[DeviceDefinition]]] = {}
    
    # Discover node type keys dynamically (e.g., "p", "pe", "spine", "leaf")
    node_type_keys = self._discover_node_type_keys(group_vars)
    self.logger.info("Discovered node types: %s", sorted(node_type_keys))
    
    # Parse devices from group variables
    for group_name, group_data in group_vars.items():
        # Determine fabric_name
        fabric_name = self._resolve_fabric_name(group_data, group_vars, global_vars)
        
        if fabric_name not in devices_by_fabric:
            devices_by_fabric[fabric_name] = {}
        
        # Check each discovered node type key
        for node_type_key in node_type_keys:
            if node_type_key in group_data:
                # Parse devices for this node type
                devices = self._parse_topology_section(
                    group_data[node_type_key],
                    node_type_key,  # Use key as device_type (e.g., "p", "pe")
                    fabric_name,
                    host_vars
                )
                
                # Add to devices_by_fabric
                if node_type_key not in devices_by_fabric[fabric_name]:
                    devices_by_fabric[fabric_name][node_type_key] = []
                devices_by_fabric[fabric_name][node_type_key].extend(devices)
    
    # Create fabric definitions with flexible devices_by_type
    for fabric_name, devices_dict in devices_by_fabric.items():
        fabric = FabricDefinition(
            name=fabric_name,
            design_type=self._detect_design_type(group_vars, global_vars),
            devices_by_type=devices_dict  # {"p": [...], "pe": [...]} or {"spine": [...], "leaf": [...]}
        )
        fabrics.append(fabric)
    
    return fabrics

def _detect_design_type(
    self,
    group_vars: Dict[str, Dict[str, Any]],
    global_vars: Dict[str, Any]
) -> str:
    """Detect design type from inventory variables.
    
    Checks for design.type key or infers from routing protocols.
    
    Returns
    -------
    str
        Design type: "l3ls-evpn", "mpls", "l2ls", or "unknown"
    """
    # Check for explicit design.type
    for group_data in group_vars.values():
        if "design" in group_data and "type" in group_data["design"]:
            return group_data["design"]["type"]
    
    # Infer from underlay_routing_protocol
    for group_data in group_vars.values():
        underlay = group_data.get("underlay_routing_protocol", "")
        if "isis-sr" in underlay or "isis" in underlay:
            return "mpls"
        if "ebgp" in underlay or "bgp" in underlay:
            return "l3ls-evpn"
    
    return "unknown"
```

**Example: MPLS Inventory Processing**

```python
# Given: examples/eos-design-mpls inventory structure
# group_vars/backbone/p-nodes.yml contains "p:" key
# group_vars/backbone/pe-nodes.yml contains "pe:" key

loader = InventoryLoader()
inventory = loader.load(Path("examples/eos-design-mpls"))

# Discovered node types: ["p", "pe"]
# Fabric: backbone
# Design type: mpls (detected from isis-sr underlay)
# devices_by_type: {
#     "p": [s1-p01, s1-p02, s2-p01, s2-p02],
#     "pe": [s1-pe01, s1-pe02, s1-pe03, s1-pe04, s2-pe01]
# }

fabric = inventory.fabrics[0]
assert fabric.name == "backbone"
assert fabric.design_type == "mpls"
assert len(fabric.get_devices_by_type("p")) == 4
assert len(fabric.get_devices_by_type("pe")) == 5
assert len(fabric.spine_devices) == 0  # No spines in MPLS design
```

### Schema Utility Module

The application shall provide a `avd_cli.utils.schema` module to centralize schema constant loading:

```python
# avd_cli/utils/schema.py
"""Schema utilities for loading constants from py-avd."""

from typing import List, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Fallback constants (used when py-avd is unavailable)
_FALLBACK_PLATFORMS = [
    "vEOS-lab",
    "vEOS",
    "cEOS",
    "cEOSLab",
    "7050X3",
    "7280R3",
    "7500R3",
    "7800R3",
]

_FALLBACK_DEVICE_TYPES = [
    "spine",
    "leaf",
    "border_leaf",
    "super_spine",
    "overlay_controller",
    "wan_router",
]

@lru_cache(maxsize=1)
def get_supported_platforms() -> List[str]:
    """Get list of supported EOS platforms.

    Attempts to load from py-avd schema. Falls back to hardcoded list
    if py-avd is unavailable or import fails.

    Returns
    -------
    List[str]
        List of supported platform names

    Examples
    --------
    >>> platforms = get_supported_platforms()
    >>> "vEOS-lab" in platforms
    True
    """
    try:
        from pyavd._eos_designs.schema import AvdSchema

        # Extract platform names from schema
        schema = AvdSchema()
        platforms = schema.get_platforms()

        logger.info(f"Loaded {len(platforms)} platforms from py-avd schema")
        return platforms

    except (ImportError, AttributeError) as e:
        logger.warning(
            f"Could not load platforms from py-avd: {e}. "
            f"Using fallback list."
        )
        return _FALLBACK_PLATFORMS

@lru_cache(maxsize=1)
def get_supported_device_types() -> List[str]:
    """Get list of supported device types.

    Attempts to load from py-avd schema. Falls back to hardcoded list
    if py-avd is unavailable or import fails.

    Returns
    -------
    List[str]
        List of supported device type names

    Examples
    --------
    >>> types = get_supported_device_types()
    >>> "spine" in types
    True
    """
    try:
        from pyavd._eos_designs.schema import AvdSchema

        # Extract device types from schema
        schema = AvdSchema()
        device_types = schema.get_device_types()

        logger.info(f"Loaded {len(device_types)} device types from py-avd schema")
        return device_types

    except (ImportError, AttributeError) as e:
        logger.warning(
            f"Could not load device types from py-avd: {e}. "
            f"Using fallback list."
        )
        return _FALLBACK_DEVICE_TYPES

@lru_cache(maxsize=1)
def get_avd_schema_version() -> Optional[str]:
    """Get py-avd schema version.

    Returns
    -------
    Optional[str]
        Schema version string, or None if py-avd unavailable

    Examples
    --------
    >>> version = get_avd_schema_version()
    >>> version is None or isinstance(version, str)
    True
    """
    try:
        from pyavd import __version__
        return __version__
    except ImportError:
        logger.debug("py-avd not available, schema version unknown")
        return None

def clear_schema_cache() -> None:
    """Clear cached schema values.

    Useful for testing or when py-avd is dynamically loaded.

    Examples
    --------
    >>> clear_schema_cache()
    >>> platforms = get_supported_platforms()  # Will reload from schema
    """
    get_supported_platforms.cache_clear()
    get_supported_device_types.cache_clear()
    get_avd_schema_version.cache_clear()
```

### Loading Valid Inventory

```python
from avd_cli.models.inventory import InventoryLoader

loader = InventoryLoader()
inventory = loader.load(Path("./inventory"))

print(f"Loaded {len(inventory.get_all_devices())} devices")
for fabric in inventory.fabrics:
    print(f"Fabric: {fabric.name}")
    print(f"  Spines: {len(fabric.spine_devices)}")
    print(f"  Leafs: {len(fabric.leaf_devices)}")
```

### Using Schema Constants from py-avd

```python
from avd_cli.utils.schema import (
    get_supported_platforms,
    get_supported_device_types,
    get_avd_schema_version,
)

# Get dynamically loaded constants
platforms = get_supported_platforms()
print(f"Supported platforms: {platforms}")

device_types = get_supported_device_types()
print(f"Supported device types: {device_types}")

# Check schema version
schema_version = get_avd_schema_version()
print(f"Using AVD schema version: {schema_version}")
```

### Loading Directory-Based Variables

The loader shall support loading variables from directories containing multiple YAML files:

```python
from pathlib import Path
from avd_cli.logics.loader import InventoryLoader

loader = InventoryLoader()

# Example 1: Loading group_vars from directory
# inventory/group_vars/atd/
#   ├── basics.yml
#   ├── aaa.yml
#   ├── platform.yml
#   └── ntp.yml

group_vars = loader._load_group_vars(Path("inventory"))

# All files merged in alphabetical order: aaa.yml -> basics.yml -> ntp.yml -> platform.yml
# Later files override earlier ones for duplicate keys
assert "hostname" in group_vars["atd"]  # from basics.yml
assert "aaa" in group_vars["atd"]  # from aaa.yml
assert "ntp" in group_vars["atd"]  # from ntp.yml

# Example 2: Mixed format support
# inventory/group_vars/
#   ├── all/                    # Directory
#   │   ├── basics.yml
#   │   └── defaults.yml
#   ├── FABRIC.yml              # Single file
#   └── SPINES/                 # Directory
#       ├── topology.yml
#       └── bgp.yml

group_vars = loader._load_group_vars(Path("inventory"))
assert "all" in group_vars  # Loaded from directory
assert "FABRIC" in group_vars  # Loaded from file
assert "SPINES" in group_vars  # Loaded from directory
```

### Deep Merge Implementation

When merging variables from multiple files, dictionaries shall be merged recursively:

```python
def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Parameters
    ----------
    base : Dict[str, Any]
        Base dictionary (earlier file)
    override : Dict[str, Any]
        Override dictionary (later file)

    Returns
    -------
    Dict[str, Any]
        Merged dictionary with override values taking precedence

    Examples
    --------
    >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
    >>> override = {"b": {"d": 4, "e": 5}, "f": 6}
    >>> deep_merge(base, override)
    {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge(result[key], value)
        else:
            # Override or add new key
            result[key] = value

    return result

# Example usage with multiple files
# File 1: basics.yml
basics = {
    "hostname": "{{ inventory_hostname }}",
    "spanning_tree": {
        "mode": "mstp",
        "priority": 16384
    }
}

# File 2: overrides.yml
overrides = {
    "spanning_tree": {
        "priority": 4096,  # Override priority
        "bpduguard": True   # Add new key
    },
    "timezone": "UTC"  # Add new top-level key
}

merged = deep_merge(basics, overrides)
# Result:
# {
#     "hostname": "{{ inventory_hostname }}",
#     "spanning_tree": {
#         "mode": "mstp",           # Kept from basics
#         "priority": 4096,         # Overridden
#         "bpduguard": True         # Added
#     },
#     "timezone": "UTC"             # Added
# }
```

### Handling Validation Errors

```python
from avd_cli.models.inventory import InventoryValidator

validator = InventoryValidator()
result = validator.validate(inventory)

if result.has_errors:
    console.print("[red]Validation failed:[/red]")
    for error in result.errors:
        console.print(f"  {error}")
    sys.exit(1)

if result.has_warnings:
    console.print("[yellow]Warnings:[/yellow]")
    for warning in result.warnings:
        console.print(f"  {warning}")
```

### Edge Cases

#### Empty Inventory

```python
# Given: Directory exists but contains no devices
# Expected: Validation error with helpful message
result = validator.validate(empty_inventory)
assert result.has_errors
assert "No devices found" in str(result.errors[0])
```

#### Partial YAML

```python
# Given: Device definition missing required fields
# Expected: Clear error listing missing fields
yaml_content = """
hostname: spine1
platform: vEOS-lab
# Missing: mgmt_ip, device_type, fabric
"""
# Validation error: "Missing required fields: mgmt_ip, device_type, fabric"
```

#### Mixed IP Versions

```python
# Given: Inventory with both IPv4 and IPv6 addresses
# Expected: Both formats supported
device1 = DeviceDefinition(
    hostname="spine1",
    mgmt_ip=IPv4Address("192.168.0.10"),
    ...
)
device2 = DeviceDefinition(
    hostname="spine2",
    mgmt_ip=IPv6Address("2001:db8::10"),
    ...
)
assert isinstance(device1.mgmt_ip, IPv4Address)
assert isinstance(device2.mgmt_ip, IPv6Address)
```

## 10. Validation Criteria

### Schema Compliance

- **VAL-001**: All required fields present in device definitions
- **VAL-002**: All field types match declared types
- **VAL-003**: IP addresses are valid format
- **VAL-004**: Hostnames follow naming conventions

### Data Integrity

- **VAL-005**: No duplicate hostnames in inventory
- **VAL-006**: No duplicate management IPs
- **VAL-007**: Cross-references are valid (e.g., MLAG peers exist)
- **VAL-008**: Group inheritance resolves correctly

### Error Reporting

- **VAL-009**: Validation errors include file paths
- **VAL-010**: Error messages include line numbers for YAML errors
- **VAL-011**: Suggestions provided for common errors
- **VAL-012**: All errors collected before failing (not fail-fast)

## 11. Related Specifications / Further Reading

### Internal Specifications

- [Tool: AVD CLI Architecture](./tool-avd-cli-architecture.md)
- [Process: AVD Workflow](./process-avd-workflow.md)

### External Documentation

- [AVD Schema Documentation](https://avd.arista.com/5.7/roles/eos_designs/)
- [Ansible Inventory Structure](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Python ipaddress Module](https://docs.python.org/3/library/ipaddress.html)
- [YAML 1.2 Specification](https://yaml.org/spec/1.2/spec.html)
