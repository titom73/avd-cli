# deploy Command

Deploy configurations to Arista EOS devices via eAPI with validation and diff support.

---

## Synopsis

```bash
avd-cli deploy eos [OPTIONS]
```

---

## Common Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to Ansible inventory directory |
| `--configs-path` | `-c` | Path | Auto | Path to configuration files (default: `<inventory>/intended/configs`) |
| `--dry-run` | | Flag | `false` | Preview changes without applying them |
| `--diff` | | Flag | `false` | Display full configuration differences |
| `--verify-ssl` | | Flag | `false` | Enable SSL certificate verification |
| `--limit-to-groups` | `-l` | Text | All | Deploy to specific groups only (repeatable) |
| `--verbose` | `-v` | Flag | `false` | Show detailed deployment progress |

See [Environment Variables](../environment-variables.md) for configuration via environment variables.

**Required variables in your inventory:**

- `ansible_user` - Username for eAPI authentication
- `ansible_password` - Password for eAPI authentication

**Variable precedence:**

1. Host-level variables (highest priority)
2. Group-level variables

---

## Quick Start

### Basic Deployment

Deploy all configurations with validation:

```bash
avd-cli deploy eos -i ./inventory
```

### Preview Changes (Recommended)

Always preview changes before applying:

```bash
avd-cli deploy eos -i ./inventory --dry-run --diff
```

### Production Deployment

Deploy with SSL verification enabled:

```bash
avd-cli deploy eos -i ./inventory --verify-ssl
```

---

## Key Features

### 🔍 Dry-Run Mode

Preview configuration changes without modifying devices.

```bash
avd-cli deploy eos -i ./inventory --dry-run
```

**What happens:**

- ✅ Connects to devices
- ✅ Generates configuration diffs
- ✅ Validates configurations
- ❌ Does NOT apply changes

!!! tip "Best Practice"
    Always run with `--dry-run` first to validate changes before live deployment.

### 📊 Configuration Diff

Display detailed configuration differences:

```bash
avd-cli deploy eos -i ./inventory --diff
```

**Output example:**

```diff
spine-1:
--- running-config
+++ intended-config
@@ -10,7 +10,7 @@
 hostname spine-1
 !
 interface Ethernet1
-   description old description
+   description new description
    no switchport
```

!!! note
    Diff statistics (lines added/removed) are always shown in the status table. The `--diff` flag displays the full unified diff for each device.

### 🔒 SSL Verification

Enable SSL certificate verification for secure production deployments:

=== "Lab Environment"
    ```bash
    # Default - SSL verification disabled
    avd-cli deploy eos -i ./inventory
    ```

    Suitable for lab/dev environments with self-signed certificates.

=== "Production"
    ```bash
    # Enable SSL verification
    avd-cli deploy eos -i ./inventory --verify-ssl
    ```

    Required for production to prevent man-in-the-middle attacks.

---

## Advanced Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--no-session` | Flag | `false` | Skip config session validation (faster but riskier) |
| `--max-concurrent` | Integer | 10 | Maximum concurrent device deployments |
| `--timeout` | Integer | 30 | Connection timeout in seconds |

---

## Deployment Workflow

The deployment process follows these steps:

1. **Load Inventory**: Parse Ansible inventory to discover devices and credentials
2. **Load Configurations**: Read device configuration files from configs directory
3. **Connect**: Establish eAPI connections to target devices
4. **Validate**: Apply configs in a temporary session for validation (default)
5. **Deploy**: Commit validated configurations to devices
6. **Report**: Display results with diff statistics and errors

---

## Configuration Validation

### Default Mode (Recommended)

By default, configurations are validated using **EOS config sessions** before being applied:

```bash
avd-cli deploy eos -i ./inventory
```

**How it works:**

1. Creates temporary config session
2. Applies configuration to session
3. Validates syntax and semantics
4. Commits if valid, automatically rolls back if invalid

!!! success "Recommended for Production"
    Config session validation provides safety and automatic rollback.

### Fast Mode (Lab Only)

Skip validation for faster deployment in lab environments:

```bash
avd-cli deploy eos -i ./inventory --no-session
```

!!! warning "Use with Caution"
    - No validation performed
    - No automatic rollback
    - Invalid config can disrupt device operation
    - **Only use in lab environments**

---

## Credentials

Credentials are extracted from Ansible inventory variables:

```yaml title="inventory.yml"
all:
  children:
    spines:
      vars:
        ansible_user: admin
        ansible_password: admin123
      hosts:
        spine-1:
          ansible_host: 192.168.0.10
```

---

## Usage Examples

### Incremental Group Deployment

Deploy to groups separately for safer rollouts:

```bash
# Deploy spines first
avd-cli deploy eos -i ./inventory -l spines --dry-run
avd-cli deploy eos -i ./inventory -l spines

# Then deploy leafs
avd-cli deploy eos -i ./inventory -l leafs --dry-run
avd-cli deploy eos -i ./inventory -l leafs
```

### Custom Configuration Path

Use a custom configuration directory:

```bash
avd-cli deploy eos -i ./inventory -c ./custom-configs
```

Configuration files must be named `<hostname>.cfg`.

### High Concurrency Deployment

Deploy to many devices simultaneously:

```bash
avd-cli deploy eos -i ./inventory --max-concurrent 20
```

### Extended Timeout

Increase timeout for slow networks or large configurations:

```bash
avd-cli deploy eos -i ./inventory --timeout 120
```

---

## Output

### Deployment Plan

```
Deployment Plan (live deployment)
  Mode: merge
  Targets: 4 devices
  Concurrency: 10
  Credentials: admin / ********

⠼ Deploying to 4 devices...
```

### Results Table

```
                      Deployment Status
┌────────────┬──────────┬──────────┬────────────┬────────────────────────┐
│ Hostname   │ Status   │ Duration │ Diff (+/-) │ Error                  │
├────────────┼──────────┼──────────┼────────────┼────────────────────────┤
│ spine-1    │ success  │ 2.34s    │ +15 / -3   │                        │
│ spine-2    │ success  │ 1.89s    │ +45 / -10  │                        │
│ leaf-1     │ success  │ 3.12s    │ +12 / -2   │                        │
│ leaf-2     │ failed   │ 5.00s    │ -          │ Connection timeout     │
└────────────┴──────────┴──────────┴────────────┴────────────────────────┘

Summary:
  ✓ Success: 3
  ✗ Failed: 1

⚠  1 deployment(s) failed
```

**Columns:**

- **Status**: `success`, `failed`, or `skipped`
- **Duration**: Time taken for deployment
- **Diff (+/-)**: Configuration changes (additions in green, deletions in red)
- **Error**: Failure reason if applicable

### Full Diff Output (--diff)

With `--diff` flag, view complete configuration changes:

```diff
spine-1:
--- running-config
+++ intended-config
@@ -10,7 +10,7 @@
 hostname spine-1
 !
 interface Ethernet1
-   description old description
+   description new description
    no switchport
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | All deployments successful |
| 1 | One or more deployments failed |

---


## Best Practices

!!! success "1. Always Dry-Run First"
    Preview changes before applying:
    ```bash
    avd-cli deploy eos -i ./inventory --dry-run --diff
    ```

!!! success "2. Incremental Deployment"
    Deploy to groups separately:
    ```bash
    # Spines first
    avd-cli deploy eos -i ./inventory -l spines

    # Then leafs
    avd-cli deploy eos -i ./inventory -l leafs
    ```

!!! success "3. Version Control"
    Commit configurations before deployment:
    ```bash
    git add inventory/intended/configs/
    git commit -m "feat: update OSPF configuration"
    git push
    ```

!!! success "4. Test in Lab First"
    Validate in non-production environment:
    ```bash
    # Lab
    avd-cli deploy eos -i ./lab-inventory --dry-run

    # Production (with SSL)
    avd-cli deploy eos -i ./prod-inventory --verify-ssl
    ```

!!! success "5. Backup Configurations"
    Always backup before major changes:
    ```bash
    ansible-playbook backup-configs.yml -i inventory/inventory.yml
    ```

!!! success "6. Use Config Session Validation"
    Enable validation for production (default):
    ```bash
    # Production - with validation
    avd-cli deploy eos -i ./inventory

    # Lab only - skip validation for speed
    avd-cli deploy eos -i ./lab-inventory --no-session
    ```

!!! success "7. Adjust Timeouts"
    Set appropriate timeouts based on network:

    - Lab/Fast: 30s (default)
    - Production/WAN: 60-120s
    - Large configs: 120s+

    ```bash
    avd-cli deploy eos -i ./inventory --timeout 120
    ```

!!! success "8. Secure Credentials"
    Use Ansible Vault for sensitive data:
    ```bash
    ansible-vault encrypt_string 'password' --name 'ansible_password'
    ```

!!! success "9. Limit Concurrency"
    Don't overwhelm production devices:
    ```bash
    avd-cli deploy eos -i ./prod-inventory --max-concurrent 5
    ```

---

## CI/CD Integration

### GitHub Actions

```yaml title=".github/workflows/deploy.yml"
name: Deploy Configurations

on:
  push:
    branches: [main]
    paths: ['inventory/intended/configs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install avd-cli
        run: pip install avd-cli

      - name: Dry-run
        run: avd-cli deploy eos -i ./inventory --dry-run --diff

      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: avd-cli deploy eos -i ./inventory --verify-ssl
```

### GitLab CI

```yaml title=".gitlab-ci.yml"
deploy:
  stage: deploy
  script:
    - pip install avd-cli
    - avd-cli deploy eos -i ./inventory --dry-run --diff
    - avd-cli deploy eos -i ./inventory --verify-ssl
  only:
    - main
  changes:
    - inventory/intended/configs/**
```

---

## See Also

- [generate Command](./generate.md) - Generate configurations before deployment
- [validate Command](./validate.md) - Validate inventory structure
- [Environment Variables](../environment-variables.md) - Configuration options
- [Workflows](../workflows.md) - Understanding AVD workflows
