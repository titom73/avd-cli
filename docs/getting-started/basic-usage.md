# Basic Usage

Learn the fundamentals of using AVD CLI effectively.

---

## Command Structure

AVD CLI follows a simple command structure:

```bash
avd-cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options

```bash
avd-cli --help      # Show help message
avd-cli --version   # Show version information
```

---

## Core Commands

AVD CLI provides four main commands:

| Command | Purpose | Common Use Case |
|---------|---------|-----------------|
| `generate` | Generate configs, docs, or tests | Main workflow command |
| `info` | Display inventory information | Quick inventory overview |
| `validate` | Validate inventory structure | Pre-flight checks |

---

## The `generate` Command

The most commonly used command for generating network configurations and documentation.

### Subcommands

```bash
avd-cli generate all        # Generate everything (configs + docs + tests)
avd-cli generate configs    # Generate configurations only
avd-cli generate docs       # Generate documentation only
avd-cli generate tests      # Generate test files only
```

### Basic Example

```bash
# Generate all outputs
avd-cli generate all \
  --inventory-path ./my-network \
  --output-path ./output

# Short form using aliases
avd-cli generate all -i ./my-network -o ./output
```

### Common Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--inventory-path` | `-i` | Path to AVD inventory | *Required* |
| `--output-path` | `-o` | Output directory | *Required* |
| `--workflow` | | Workflow type (`eos-design` or `cli-config`) | `eos-design` |
| `--limit-to-groups` | `-l` | Limit to specific device groups | All groups |
| `--show-deprecation-warnings` | | Show pyavd deprecation warnings | `false` |

### Examples

```bash
# Generate with specific workflow
avd-cli generate all -i ./inventory -o ./output --workflow eos-design

# Generate for specific groups only
avd-cli generate all -i ./inventory -o ./output -l SPINES -l LEAFS

# Show deprecation warnings
avd-cli generate configs -i ./inventory -o ./output --show-deprecation-warnings
```

---

## The `info` Command

Display detailed information about your inventory.

### Basic Usage

```bash
# Display inventory summary
avd-cli info --inventory-path ./my-network

# Use JSON output format
avd-cli info -i ./my-network --format json

# Use YAML output format
avd-cli info -i ./my-network --format yaml
```

### Output Formats

=== "Table (Default)"
    ```bash
    avd-cli info -i ./inventory

```

    Displays a formatted table with device information, fabric details, and summary statistics.

=== "JSON"
    ```bash
    avd-cli info -i ./inventory --format json
```

    ```json
    {
      "fabrics": [
        {
          "name": "MY_FABRIC",
          "design_type": "l3ls-evpn",
          "devices": [...]
        }
      ]
    }
    ```

=== "YAML"
    ```bash
    avd-cli info -i ./inventory --format yaml

```

    ```yaml
    fabrics:
      - name: MY_FABRIC
        design_type: l3ls-evpn
        devices: [...]
    ```

---

## The `validate` Command

Validate your inventory structure before generation.

### Basic Usage

```bash
# Validate inventory
avd-cli validate --inventory-path ./my-network

# Verbose validation
avd-cli validate -i ./my-network --verbose
```

### What Gets Validated

- ✅ Inventory file existence and syntax
- ✅ Required group_vars files
- ✅ Fabric topology structure
- ✅ Spine device presence (for eos-design workflow)
- ✅ Variable hierarchy and inheritance
- ✅ Jinja2 template syntax

### Example Output

```
→ Validating inventory structure...
✓ Inventory file found: inventory.yml
✓ Group variables found: group_vars/FABRIC.yml
✓ Fabric topology validated: MY_FABRIC
✓ Found 2 spine devices
✓ Found 2 leaf devices

✓ Validation successful!
```

---

## Environment Variables

All CLI options can be set using environment variables with the `AVD_CLI_` prefix.

### Setting Environment Variables

```bash
# Set inventory and output paths
export AVD_CLI_INVENTORY_PATH=./my-network
export AVD_CLI_OUTPUT_PATH=./output

# Set workflow
export AVD_CLI_WORKFLOW=eos-design

# Set device groups
export AVD_CLI_LIMIT_TO_GROUPS=SPINES,LEAFS

# Now run commands without repeating options
avd-cli generate all
avd-cli info
```

### Variable Reference

| CLI Option | Environment Variable | Example Value |
|-----------|---------------------|---------------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | `./output` |
| `--workflow` | `AVD_CLI_WORKFLOW` | `eos-design` |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | `SPINES,LEAFS` |
| `--format` | `AVD_CLI_FORMAT` | `json` |
| `--show-deprecation-warnings` | `AVD_CLI_SHOW_DEPRECATION_WARNINGS` | `true` |

!!! tip "Priority Order"
    CLI arguments > Environment variables > Default values

---

## Output Directory Structure

When you run `generate all`, AVD CLI creates the following structure:

```
output/
├── configs/              # Device configurations (.cfg files)
│   ├── spine1.cfg
│   ├── spine2.cfg
│   └── ...
├── documentation/        # Generated documentation
│   ├── devices/         # Per-device documentation
│   │   ├── spine1.md
│   │   └── ...
│   └── fabric/          # Fabric-wide documentation
│       └── FABRIC-documentation.md
└── tests/               # Test files (ANTA or Robot)
    ├── device1_tests.yaml
    ├── device2_tests.yaml
    └── ...
```

---

## Common Workflows

### Development Workflow

```bash
# 1. Validate before generating
avd-cli validate -i ./inventory

# 2. Generate configs to test
avd-cli generate configs -i ./inventory -o ./output

# 3. If all looks good, generate everything
avd-cli generate all -i ./inventory -o ./output
```

### CI/CD Workflow

```bash
# Use environment variables in CI/CD
export AVD_CLI_INVENTORY_PATH="${CI_PROJECT_DIR}/inventory"
export AVD_CLI_OUTPUT_PATH="${CI_PROJECT_DIR}/output"
export AVD_CLI_WORKFLOW=eos-design

# Validate
avd-cli validate

# Generate
avd-cli generate all

# Output files are now in ${CI_PROJECT_DIR}/output
```

### Incremental Updates

```bash
# Only process spine devices
avd-cli generate configs -i ./inventory -o ./output -l SPINES

# Only process a specific rack
avd-cli generate all -i ./inventory -o ./output -l RACK1
```

---

## Getting Help

### Command-Specific Help

```bash
# General help
avd-cli --help

# Command help
avd-cli generate --help
avd-cli generate configs --help
avd-cli info --help
avd-cli validate --help
```

### Verbose Output

Enable verbose output for debugging:

```bash
avd-cli validate -i ./inventory --verbose
avd-cli info -i ./inventory --verbose
```

---

## Next Steps

Now that you understand the basics:

- Learn about [Advanced Commands](../user-guide/commands/overview.md)
- Understand [Inventory Structure](../user-guide/inventory-structure.md)
- Explore [Workflows](../user-guide/workflows.md)
- See [Real-World Examples](../examples/basic.md)

---

!!! question "Need Help?"
    - Check the [FAQ](../faq.md)
    - Review [detailed command documentation](../user-guide/commands/overview.md)
    - Open an issue on [GitHub](https://github.com/titom73/avd-cli/issues)
