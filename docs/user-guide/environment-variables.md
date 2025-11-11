# Environment Variables

All AVD CLI options support environment variables with the `AVD_CLI_` prefix.

---

## Common Options

These variables apply across multiple commands:

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | Path | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | Path | `./output` |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | Comma-separated | `SPINES,LEAFS` |

---

## Generate Command

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `--workflow` | `AVD_CLI_WORKFLOW` | Choice | `eos-design`, `cli-config` |
| `--show-deprecation-warnings` | `AVD_CLI_SHOW_DEPRECATION_WARNINGS` | Boolean | `true`, `false` |
| `--test-type` | `AVD_CLI_TEST_TYPE` | Choice | `anta`, `robot` |

---

## Deploy Command

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `-c, --configs-path` | `AVD_CLI_CONFIGS_PATH` | Path | `./configs` |
| `--dry-run` | `AVD_CLI_DRY_RUN` | Boolean | `true`, `false` |
| `--diff` | `AVD_CLI_SHOW_DIFF` | Boolean | `true`, `false` |
| `--verify-ssl` | `AVD_CLI_VERIFY_SSL` | Boolean | `true`, `false` |
| `--no-session` | `AVD_CLI_NO_SESSION` | Boolean | `true`, `false` |
| `--max-concurrent` | `AVD_CLI_MAX_CONCURRENT` | Integer | `10` |
| `--timeout` | `AVD_CLI_TIMEOUT` | Integer | `30` |

---

## Info Command

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `--format` | `AVD_CLI_FORMAT` | Choice | `table`, `json`, `yaml` |

---

## Usage Examples

### Basic Setup

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_OUTPUT_PATH=./output

# Now run without repeating options
avd-cli generate all
avd-cli validate
```

### Deployment Configuration

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_DRY_RUN=true
export AVD_CLI_SHOW_DIFF=true
export AVD_CLI_VERIFY_SSL=false

# Preview deployment
avd-cli deploy eos
```

### Production Deployment

```bash
export AVD_CLI_INVENTORY_PATH=./prod-inventory
export AVD_CLI_VERIFY_SSL=true
export AVD_CLI_TIMEOUT=120
export AVD_CLI_MAX_CONCURRENT=5

# Secure production deployment
avd-cli deploy eos
```

### CI/CD Environment

```bash
#!/bin/bash
# CI pipeline environment setup

export AVD_CLI_INVENTORY_PATH="${CI_PROJECT_DIR}/inventory"
export AVD_CLI_OUTPUT_PATH="${CI_PROJECT_DIR}/output"
export AVD_CLI_WORKFLOW=eos-design
export AVD_CLI_DRY_RUN=true

# Validate and generate
avd-cli validate
avd-cli generate all
avd-cli deploy eos --dry-run --diff
```

---

## Notes

!!! info "Precedence"
    Command-line arguments always override environment variables.

!!! tip "Boolean Values"
    For boolean flags, use `true` or `false` (case-insensitive).

!!! tip "Multiple Groups"
    For `AVD_CLI_LIMIT_TO_GROUPS`, separate groups with commas: `SPINES,LEAFS,BORDER`

---

## See Also

- [Basic Usage](../getting-started/basic-usage.md) - Getting started guide
- [Commands Overview](./commands/overview.md) - All available commands
