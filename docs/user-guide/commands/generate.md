# generate Command

Generate network configurations, documentation, and ANTA tests from your AVD inventory.

---

## Synopsis

```bash
avd-cli generate SUBCOMMAND [OPTIONS]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `all` | Generate configurations, documentation, and tests |
| `configs` | Generate device configurations only |
| `docs` | Generate documentation only |
| `tests` | Generate ANTA test files only |
| `topology containerlab` | Generate Containerlab topology from AVD inventory |

---

## Common Options

These options apply to all `generate` subcommands:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to AVD inventory directory |
| `--output-path` | `-o` | Path | *Required* | Output directory for generated files |
| `--limit` | `-l` | Text | All | Filter devices by hostname or group patterns (repeatable, supports wildcards) |
| `--limit-to-groups` | | Text | All | **Deprecated**. Use `--limit` instead. Limit to specific groups |
| `--workflow` | | Choice | `eos-design` | Workflow type: `eos-design` or `cli-config` |
| `--show-deprecation-warnings` | | Flag | `false` | Show pyavd deprecation warnings |

---

## generate all

Generate all outputs: configurations, documentation, and tests.

### Usage

```bash
avd-cli generate all -i INVENTORY_PATH -o OUTPUT_PATH [OPTIONS]
```

### Examples

```bash
# Basic usage
avd-cli generate all -i ./inventory -o ./output

# With specific workflow
avd-cli generate all -i ./inventory -o ./output --workflow eos-design

# Filter by group names
avd-cli generate all -i ./inventory -o ./output -l SPINES -l LEAFS

# Filter by hostname patterns (wildcards supported)
avd-cli generate all -i ./inventory -o ./output -l "spine*"

# Filter by specific hostnames
avd-cli generate all -i ./inventory -o ./output -l spine-01 -l leaf-1a

# Mix hostname and group filters
avd-cli generate all -i ./inventory -o ./output -l "spine*" -l BORDER_LEAFS

# Show deprecation warnings
avd-cli generate all -i ./inventory -o ./output --show-deprecation-warnings
```

### Output Structure

```
output/
├── configs/
│   └── *.cfg                   # Device configurations
├── documentation/
│   ├── devices/
│   │   └── *.md                # Per-device documentation
│   └── fabric/
│       └── *-documentation.md  # Fabric-wide documentation
└── tests/
    ├── device1_tests.yaml      # ANTA tests for device1
    ├── device2_tests.yaml      # ANTA tests for device2
    └── ...                     # One test file per device
```

---

## generate configs

Generate device configurations only.

### Usage

```bash
avd-cli generate configs -i INVENTORY_PATH -o OUTPUT_PATH [OPTIONS]
```

### Examples

```bash
# Generate all device configurations
avd-cli generate configs -i ./inventory -o ./output

# Filter by group name
avd-cli generate configs -i ./inventory -o ./output -l SPINES

# Filter by hostname pattern
avd-cli generate configs -i ./inventory -o ./output -l "spine-*"

# Filter specific devices
avd-cli generate configs -i ./inventory -o ./output -l spine-01 -l spine-02

# Use cli-config workflow (skip eos_design role)
avd-cli generate configs -i ./inventory -o ./output --workflow cli-config
```

### Workflows

=== "eos-design"
    Full AVD pipeline with topology design and validation:
    ```bash
    avd-cli generate configs -i ./inventory -o ./output --workflow eos-design

```

    - Runs `eos_design` role to generate structured configs
    - Validates topology structure
    - Generates device configurations

=== "cli-config"
    Direct configuration generation from existing structured configs:
    ```bash
    avd-cli generate configs -i ./inventory -o ./output --workflow cli-config
```

    - Skips `eos_design` role
    - Uses existing structured configs from `host_vars/`
    - Faster for iterative testing

---

## generate docs

Generate network documentation only.

### Usage

```bash
avd-cli generate docs -i INVENTORY_PATH -o OUTPUT_PATH [OPTIONS]
```

### Examples

```bash
# Generate all documentation
avd-cli generate docs -i ./inventory -o ./output

# Filter by group name
avd-cli generate docs -i ./inventory -o ./output -l RACK1

# Filter by hostname pattern
avd-cli generate docs -i ./inventory -o ./output -l "leaf-*"

# Filter specific devices
avd-cli generate docs -i ./inventory -o ./output -l spine-01
```

### Generated Documentation

- **Per-device documentation**: Detailed device configuration documentation
- **Fabric documentation**: Fabric-wide topology and design documentation

---

## generate tests

Generate test files for network validation using the ANTA framework or Robot Framework.

### Usage

```bash
avd-cli generate tests -i INVENTORY_PATH -o OUTPUT_PATH [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--test-type` | | Choice | `anta` | Test framework: `anta` or `robot` |

### Examples

```bash
# Generate ANTA tests (one file per device)
avd-cli generate tests -i ./inventory -o ./output

# Generate Robot Framework tests
avd-cli generate tests -i ./inventory -o ./output --test-type robot

# Filter by group name
avd-cli generate tests -i ./inventory -o ./output -l SPINES

# Filter by hostname pattern
avd-cli generate tests -i ./inventory -o ./output -l "spine-*"

# Filter multiple patterns
avd-cli generate tests -i ./inventory -o ./output -l "spine*" -l "leaf-1*"
```

### ANTA Test Generation

The ANTA test generator creates comprehensive network validation tests by analyzing your AVD inventory and structured configurations. Each device receives its own test catalog file with device-specific tests.

#### Generated Test Structure

```
tests/
├── spine01_tests.yaml          # Tests for spine01
├── spine02_tests.yaml          # Tests for spine02
├── leaf-1a_tests.yaml          # Tests for leaf-1a
├── leaf-1b_tests.yaml          # Tests for leaf-1b
└── ...                         # One file per device
```

#### Test Categories

Each device test file includes the following categories when applicable:

**Connectivity Tests**

- Internet connectivity validation (8.8.8.8)
- Management interface reachability

**BGP Tests**

- BGP ASN verification
- BGP peer state validation
- Address family configuration checks

**EVPN Tests** (for EVPN-capable devices)

- EVPN peer count validation
- VNI to VLAN mapping verification
- EVPN Type-2 route checks

**Interface Tests**

- Ethernet interface status validation
- Loopback interface verification
- Management interface checks

**Hardware Tests**

- Power supply status
- Cooling system validation
- Temperature monitoring
- Transceiver manufacturer checks
- Platform-specific tests (DCS-7050, DCS-7280, DCS-7300)

**System Tests**

- Uptime validation (minimum 24 hours)
- Reload cause verification
- Core dump detection
- Agent log validation
- NTP synchronization (when configured)

#### Device Role-Based Testing

Tests are automatically adapted based on device roles:

- **Spine devices**: Focus on BGP underlay, hardware health, and system validation
- **Leaf devices**: Include EVPN overlay tests, VLAN/VNI mappings, and access connectivity
- **Border leaf devices**: Enhanced EVPN testing with external routing validation

#### Test Execution

Each generated test file is a complete ANTA catalog that can be executed independently:

```bash
# Execute tests for a specific device
anta nrfu --catalog spine01_tests.yaml --inventory inventory.yaml --limit spine01

# Execute all device tests in parallel
find tests/ -name "*_tests.yaml" -exec anta nrfu --catalog {} --inventory inventory.yaml \;
```

---

## generate topology containerlab

Generate a Containerlab topology file from your AVD inventory for network testing and simulation.

### Usage

```bash
avd-cli generate topology containerlab -i INVENTORY_PATH -o OUTPUT_PATH [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to AVD inventory directory |
| `--output-path` | `-o` | Path | *Required* | Output directory for topology file |
| `--limit` | `-l` | Text | All | Filter devices by hostname or group patterns (repeatable, supports wildcards) |
| `--startup-dir` | | Path | `configs` | Directory containing startup configs (relative to output path or absolute) |
| `--kind` | | Text | `ceos` | Containerlab node kind (e.g., `ceos`, `vr-arista_veos`) |
| `--image` | | Text | None | Complete Docker image string (overrides registry/name/version) |
| `--image-registry` | | Text | `arista` | Docker registry (used when --image not provided) |
| `--image-name` | | Text | `ceos` | Image name (used when --image not provided) |
| `--image-version` | | Text | `latest` | Image version/tag (used when --image not provided) |

### What Gets Generated

The command creates a Containerlab topology YAML file with:

- **Nodes**: All devices from the AVD inventory (or filtered subset)
  - Configurable node `kind` (default: `ceos`)
  - Configurable Docker `image` (default: `arista/ceos:latest`)
  - Includes management IP from `ansible_host` or `mgmt_ip`
  - References startup-config files (relative paths for portability)

- **Links**: Network connections from two sources:
  - **Ethernet interfaces**: Extracted from `ethernet_interfaces` with `peer`/`peer_interface` defined
  - **Uplink topology**: Extracted from AVD `l3leaf`/`l2leaf` structures using `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` arrays
  - Automatically deduplicated when the same link appears in both sources

### Examples

**Basic topology generation:**

```bash
avd-cli generate topology containerlab \
  -i examples/eos-design-basics \
  -o /tmp/containerlab-output
```

Output structure:
```
/tmp/containerlab-output/
├── configs/                          # Startup config directory (default)
│   ├── spine1.cfg
│   ├── spine2.cfg
│   ├── leaf1.cfg
│   └── ...
└── containerlab/
    └── containerlab-topology.yml     # Main topology file
```

**Filter specific devices:**

```bash
# Only spine switches
avd-cli generate topology containerlab -i ./inventory -o ./output -l "spine*"

# Multiple patterns
avd-cli generate topology containerlab -i ./inventory -o ./output \
  -l "spine-0[1-2]" -l "leaf-[12]?"
```

**Custom startup config location:**

```bash
# Use absolute path
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --startup-dir /opt/arista/configs

# Use relative path (relative to output-path)
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --startup-dir custom-configs
```

**Custom Docker image:**

```bash
# Use specific version
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --image-version 4.32.0F

# Use GitHub Container Registry
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --image ghcr.io/aristanetworks/ceos:4.32.0F

# Use private registry with custom image
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --image-registry harbor.example.com/network \
  --image-name ceos-custom \
  --image-version 1.2.3

# Use alternative node kind (vrnetlab)
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output \
  --kind vr-arista_veos \
  --image vrnetlab/vr-arista_veos:4.32.0F
```

### Topology File Structure

Generated `containerlab-topology.yml`:

```yaml
name: my-fabric
topology:
  nodes:
    spine1:
      kind: ceos
      image: arista/ceos:latest
      mgmt-ipv4: 192.168.0.11
      startup-config: ../configs/spine1.cfg
    leaf1:
      kind: ceos
      image: arista/ceos:latest
      mgmt-ipv4: 192.168.0.21
      startup-config: ../configs/leaf1.cfg

  links:
    # From ethernet_interfaces peer definitions
    - endpoints:
        - spine1:Ethernet1
        - leaf1:Ethernet49

    # From AVD uplink topology (l3leaf/l2leaf)
    - endpoints:
        - leaf1:Ethernet51
        - spine1:Ethernet2
```

### Link Generation Details

**Source 1: Ethernet Interfaces**

Links are extracted from devices' `ethernet_interfaces` when both are defined:
- `peer`: Remote device hostname
- `peer_interface`: Remote interface name

**Source 2: AVD Uplink Topology**

For `l3leaf` and `l2leaf` devices, links are extracted from the AVD structure:

```yaml
# In group_vars/FABRIC.yml
l3leaf:
  defaults:
    uplink_interfaces: [Ethernet1, Ethernet2]      # Local interfaces
    uplink_switches: [spine1, spine2]              # Remote devices
  node_groups:
    - nodes:
        - name: leaf1
          uplink_switch_interfaces: [Ethernet1, Ethernet2]  # Remote interfaces
```

The command automatically:
- Iterates through parallel arrays to create links
- Validates array lengths match
- Logs warnings for mismatched arrays
- Deduplicates links between both sources

### Containerlab Integration

Once generated, deploy the topology with Containerlab:

```bash
# Deploy topology
cd /tmp/containerlab-output/containerlab
sudo containerlab deploy -t containerlab-topology.yml

# Check status
sudo containerlab inspect

# Connect to a device
sudo containerlab exec -t containerlab-topology.yml --label clab-node=spine1

# Destroy topology
sudo containerlab destroy -t containerlab-topology.yml
```

### Docker Image Configuration

The Docker image is constructed based on option priority:

**Priority 1: Complete image string**
```bash
--image ghcr.io/aristanetworks/ceos:4.32.0F
# Result: image: ghcr.io/aristanetworks/ceos:4.32.0F
```

**Priority 2: Component options**
```bash
--image-registry harbor.example.com/network \
--image-name ceos-custom \
--image-version 1.2.3
# Result: image: harbor.example.com/network/ceos-custom:1.2.3
```

**Default behavior** (no options):
```bash
# Result: image: arista/ceos:latest
```

**Common scenarios:**
- Development/testing: `--image-version latest` (default)
- Production validation: `--image-version 4.32.0F`
- Private registry: `--image-registry my-registry.com/images`
- Alternative platforms: `--kind vr-arista_veos --image vrnetlab/vr-arista_veos:4.32.0F`

### Best Practices

1. **Generate configs first**: Run `avd-cli generate configs` before topology generation to ensure startup configs exist

2. **Use relative paths**: Default relative paths (`../configs/`) make topologies portable

3. **Pin image versions**: Use specific versions (e.g., `4.32.0F`) for reproducible testing environments

4. **Filter for testing**: Use `--limit` to create focused test topologies with subset of devices

5. **Version control**: Commit topology files for reproducible test environments

6. **CI/CD integration**: Generate topologies in pipelines for automated testing

### Troubleshooting

**No links generated:**

- Ensure devices have either:
  - `ethernet_interfaces` with `peer` and `peer_interface` defined, OR
  - Proper `l3leaf`/`l2leaf` structure with uplink arrays in group_vars

**Missing nodes:**

- Check device filtering with `--limit`
- Verify devices exist in AVD inventory

**Wrong config paths:**

- Default is `configs/` relative to output path
- Use `--startup-dir` to customize location
- Paths in topology file are always relative to the topology YAML file

---

## Environment Variables

All options support environment variables with the `AVD_CLI_` prefix:

| CLI Option | Environment Variable | Example |
|-----------|---------------------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | `./output` |
| `-l, --limit` | `AVD_CLI_LIMIT` | `spine*,LEAFS` |
| `--workflow` | `AVD_CLI_WORKFLOW` | `eos-design` |
| `--show-deprecation-warnings` | `AVD_CLI_SHOW_DEPRECATION_WARNINGS` | `true` |
| `--test-type` | `AVD_CLI_TEST_TYPE` | `anta` |

### Example

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_OUTPUT_PATH=./output
export AVD_CLI_WORKFLOW=eos-design

# Now run without repeating options
avd-cli generate all
```

---

## Advanced Usage

### Selective Generation

The `--limit` option supports flexible device filtering using:

- **Group names**: `SPINES`, `LEAFS`, `BORDER_LEAFS`
- **Hostname patterns**: `spine*`, `leaf-[12]*`, `border-?`
- **Exact hostnames**: `spine-01`, `leaf-1a`

**Wildcard patterns:**

- `*` - Matches any characters: `spine*` matches `spine-01`, `spine-02`, `spineA`
- `?` - Matches single character: `leaf-?` matches `leaf-1`, `leaf-a`
- `[...]` - Matches character set: `leaf-[12]a` matches `leaf-1a`, `leaf-2a`

**Examples:**

```bash
# Filter by group name
avd-cli generate all -i ./inventory -o ./output -l SPINES

# Filter by hostname pattern (all spines)
avd-cli generate all -i ./inventory -o ./output -l "spine*"

# Filter specific devices
avd-cli generate all -i ./inventory -o ./output -l spine-01 -l spine-02

# Multiple groups and patterns
avd-cli generate all -i ./inventory -o ./output -l SPINES -l "border-*" -l leaf-1a

# Complex patterns
avd-cli generate all -i ./inventory -o ./output -l "spine-0[1-3]" -l "leaf-[12]?"
```

!!! info "How Filtering Works"
    - AVD needs **all devices** for topology context (BGP neighbors, MLAG peers, etc.)
    - Filtering happens **after** AVD facts calculation
    - Only **output files** for filtered devices are generated
    - This ensures configurations are correct even when filtering single devices

### CI/CD Integration

```bash
#!/bin/bash
set -e

# Set paths
export AVD_CLI_INVENTORY_PATH="${CI_PROJECT_DIR}/inventory"
export AVD_CLI_OUTPUT_PATH="${CI_PROJECT_DIR}/output"

# Validate first
avd-cli validate

# Generate
avd-cli generate all

# Artifacts are now in $AVD_CLI_OUTPUT_PATH
```

---

## See Also

- [Workflows](../workflows.md) - Understand eos-design vs cli-config
- [Environment Variables](../environment-variables.md) - Complete variable reference
- [Examples](../../examples/basic.md) - Real-world examples
