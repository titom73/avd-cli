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

---

## Common Options

These options apply to all `generate` subcommands:

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to AVD inventory directory |
| `--output-path` | `-o` | Path | *Required* | Output directory for generated files |
| `--limit-to-groups` | `-l` | Text | All | Limit processing to specific groups (repeatable) |
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

# Limit to specific groups
avd-cli generate all -i ./inventory -o ./output -l SPINES -l LEAFS

# Show deprecation warnings
avd-cli generate all -i ./inventory -o ./output --show-deprecation-warnings
```

### Output Structure

```
output/
├── configs/
│   └── *.cfg
├── documentation/
│   ├── devices/
│   │   └── *.md
│   └── fabric/
│       └── *-documentation.md
└── tests/
    └── *-tests.yml
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

# Generate configs for spines only
avd-cli generate configs -i ./inventory -o ./output -l SPINES

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

# Generate docs for specific devices
avd-cli generate docs -i ./inventory -o ./output -l RACK1
```

### Generated Documentation

- **Per-device documentation**: Detailed device configuration documentation
- **Fabric documentation**: Fabric-wide topology and design documentation

---

## generate tests

Generate ANTA test files.

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
# Generate ANTA tests
avd-cli generate tests -i ./inventory -o ./output

# Generate Robot Framework tests
avd-cli generate tests -i ./inventory -o ./output --test-type robot
```

---

## Environment Variables

All options support environment variables with the `AVD_CLI_` prefix:

| CLI Option | Environment Variable | Example |
|-----------|---------------------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | `./output` |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | `SPINES,LEAFS` |
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

Process only specific device groups for faster iteration:

```bash
# Only spines
avd-cli generate all -i ./inventory -o ./output -l SPINES

# Multiple groups
avd-cli generate all -i ./inventory -o ./output -l SPINES -l LEAFS -l BORDER_LEAFS
```

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
