# Deploy Command

The `deploy` command group provides functionality to deploy configurations to network devices. Currently, it supports Arista EOS devices via eAPI.

## Overview

The deployment workflow:

1. **Inventory Parsing**: Reads Ansible inventory to discover devices and extract credentials
2. **Configuration Loading**: Locates configuration files for each device
3. **Connection**: Establishes eAPI connections to target devices
4. **Validation**: Optionally validates configurations in dry-run mode
5. **Deployment**: Applies configurations using replace or merge mode
6. **Reporting**: Displays results with diffs and error details

## Deploy EOS

Deploy configurations to Arista EOS devices using eAPI.

### Synopsis

```bash
avd-cli deploy eos [OPTIONS]
```

### Options

| Option | Environment Variable | Type | Default | Description |
|--------|---------------------|------|---------|-------------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | Path | Required | Path to Ansible inventory directory |
| `-c, --configs-path` | `AVD_CLI_CONFIGS_PATH` | Path | `<inventory>/intended/configs` | Path to configuration files directory |
| `--no-session` | `AVD_CLI_NO_SESSION` | Flag | False | Skip config session validation (faster but no validation) |
| `--dry-run` | `AVD_CLI_DRY_RUN` | Flag | False | Validate configurations without applying changes |
| `--diff` | `AVD_CLI_SHOW_DIFF` | Flag | False | Display configuration differences |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | Multiple | None | Limit deployment to specific groups |
| `--max-concurrent` | `AVD_CLI_MAX_CONCURRENT` | Integer | 10 | Maximum number of concurrent deployments |
| `--timeout` | `AVD_CLI_TIMEOUT` | Integer | 30 | Connection timeout in seconds |
| `--verify-ssl` | `AVD_CLI_VERIFY_SSL` | Flag | False | Verify SSL certificates |
| `-v, --verbose` | - | Flag | False | Enable verbose output |

### Configuration Deployment Modes

**Important Note:** All deployments perform **MERGE operations** - new configuration is added to or updates existing configuration, but nothing is removed. True "replace" mode (removing old config) requires file-based workflows which are not supported via eAPI.

The `--no-session` flag controls the validation behavior:

#### With Config Session Validation (Default)

By default, configurations are deployed using EOS config sessions which provide validation before committing changes. This is the **recommended and safer** approach.

**How it works:**
1. Creates a temporary config session
2. Applies configuration to the session
3. Validates syntax and semantics
4. Commits changes if validation succeeds
5. Automatically rolls back if validation fails

**Use cases:**
- Production deployments (safety-critical)
- Complex configuration changes
- When validation is important
- Initial device provisioning

**Example:**
```bash
# Default behavior - uses config session validation
avd-cli deploy eos -i ./inventory
```

#### Without Validation (--no-session)

With the `--no-session` flag, configurations are applied directly without validation. This is **faster but riskier** as invalid configuration can disrupt device operation.

**How it works:**
1. Applies configuration directly via `configure terminal`
2. No validation before applying
3. No automatic rollback on errors
4. Faster but less safe

**Use cases:**
- Lab environments where speed is prioritized
- Simple, well-tested configuration changes
- When you're confident the configuration is valid
- Incremental updates to known-good configs

**Example:**
```bash
# Direct deployment without validation (faster, riskier)
avd-cli deploy eos -i ./inventory --no-session
```

**Recommendation:** Always use config session validation (default) for production. Only use `--no-session` in lab environments when speed is more important than safety.

### Credentials

Credentials are extracted from the Ansible inventory using the following variables:

- `ansible_user`: Username for eAPI authentication
- `ansible_password`: Password for eAPI authentication

**Precedence:**
1. Host-level variables (`hosts.<hostname>.ansible_user`)
2. Group-level variables (`children.<group>.vars.ansible_user`)

**Example inventory structure:**

```yaml
all:
  children:
    spines:
      vars:
        ansible_user: admin
        ansible_password: admin123
      hosts:
        spine-1:
          ansible_host: 192.168.0.10
        spine-2:
          ansible_host: 192.168.0.11
    leafs:
      vars:
        ansible_user: netadmin
      hosts:
        leaf-1:
          ansible_host: 192.168.0.20
          ansible_password: leaf123  # Host-level password takes precedence
```

### SSL Certificate Verification

By default, SSL certificate verification is **disabled** to support lab and development environments with self-signed certificates. This allows quick testing without certificate setup.

For production deployments, enable SSL verification:

```bash
avd-cli deploy eos -i ./inventory --verify-ssl
```

**Security considerations:**
- **Lab/Dev**: Disable verification (`--verify-ssl` not specified) for convenience
- **Production**: Enable verification (`--verify-ssl`) to prevent man-in-the-middle attacks
- **Staging**: Use valid certificates and enable verification

## Examples

### Basic Deployment

Deploy configurations to all devices in the inventory:

```bash
avd-cli deploy eos -i ./inventory
```

This uses:
- Config session validation (default - recommended)
- Configuration files from `./inventory/intended/configs/`
- SSL verification disabled (lab-friendly)
- Up to 10 concurrent deployments

### Dry-Run with Diff

Validate configurations without applying changes and show differences:

```bash
avd-cli deploy eos -i ./inventory --dry-run --diff
```

This will:
- Connect to each device
- Generate configuration diffs
- Display differences
- **Not apply** any changes

### Fast Deployment (No Validation)

Deploy configurations without validation for speed (lab use only):

```bash
avd-cli deploy eos -i ./inventory --no-session
```

⚠️ **Warning:** This skips validation and is riskier. Only use in lab environments.

### Group-Limited Deployment

Deploy only to specific groups:

```bash
avd-cli deploy eos -i ./inventory -l spines -l border-leafs
```

Only devices in the `spines` and `border-leafs` groups will be deployed.

### Custom Configuration Path

Use a custom configuration directory:

```bash
avd-cli deploy eos -i ./inventory -c ./custom-configs
```

Configuration files should be named `<hostname>.cfg` in the specified directory.

### Production Deployment

Deploy to production with SSL verification:

```bash
avd-cli deploy eos -i ./prod-inventory --verify-ssl --timeout 60
```

This enables SSL verification and increases timeout for production environments.

### High Concurrency Deployment

Deploy to many devices simultaneously:

```bash
avd-cli deploy eos -i ./inventory --max-concurrent 20
```

Increases concurrent deployments from 10 (default) to 20.

### Environment Variables

Set common options via environment variables:

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_DRY_RUN=true
export AVD_CLI_SHOW_DIFF=true
export AVD_CLI_VERIFY_SSL=false

avd-cli deploy eos
```

Command-line arguments override environment variables.

## Output

The deployment command provides rich progress feedback:

### Progress Display

```
Deployment Plan (live deployment)
  Mode: replace
  Targets: 4 devices
  Concurrency: 10 devices

⠼ spine-1 - Deploying...           ████████████████████   50%   00:02
⠧ spine-2 - Deployed ✓             ████████████████████  100%   00:01
⠹ leaf-1 - Connecting...           ████░░░░░░░░░░░░░░░░   25%   00:03
⢿ leaf-2 - Connection failed ✗     ████████████████████  100%   00:05
```

### Results Table

```
┌────────────┬──────────┬──────────┬────────────────────────┐
│ Hostname   │ Status   │ Duration │ Error                  │
├────────────┼──────────┼──────────┼────────────────────────┤
│ spine-1    │ success  │ 2.34s    │                        │
│ spine-2    │ success  │ 1.89s    │                        │
│ leaf-1     │ success  │ 3.12s    │                        │
│ leaf-2     │ failed   │ 5.00s    │ Connection timeout     │
└────────────┴──────────┴──────────┴────────────────────────┘

Summary:
  ✓ Success: 3
  ✗ Failed: 1
  ○ Skipped: 0

⚠  1 deployment(s) failed
```

### Configuration Diff (--diff flag)

```
Configuration Diffs

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

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | All deployments successful |
| 1 | One or more deployments failed or deployment error occurred |

## Troubleshooting

### Connection Failures

**Problem:** `Connection failed: Connection timeout`

**Solutions:**
- Verify device IP addresses in inventory (`ansible_host`)
- Check network connectivity: `ping <device_ip>`
- Increase timeout: `--timeout 60`
- Verify eAPI is enabled on devices
- Check firewall rules for port 443

**Verify eAPI is enabled:**
```
device# show management api http-commands
```

**Enable eAPI if needed:**
```
device# configure
device(config)# management api http-commands
device(config-mgmt-api-http-cmds)# no shutdown
device(config-mgmt-api-http-cmds)# protocol https
```

### Authentication Failures

**Problem:** `Authentication failed for 192.168.0.10`

**Solutions:**
- Verify credentials in inventory (`ansible_user`, `ansible_password`)
- Check that credentials are set at host or group level
- Test credentials manually:
  ```bash
  curl -k -u admin:admin https://192.168.0.10/command-api -d '{"jsonrpc":"2.0","method":"runCmds","params":{"version":1,"cmds":["show version"],"format":"json"},"id":"1"}'
  ```

### SSL Certificate Errors

**Problem:** SSL verification fails in production

**Solutions:**
- For lab environments: Don't use `--verify-ssl` (default behavior)
- For production: Ensure valid SSL certificates are installed on devices
- Install certificates on EOS devices:
  ```
  device# copy https://ca-server/ca-cert.pem certificate:
  device# configure
  device(config)# management security
  device(config-mgmt-security)# ssl profile MGMT
  device(config-mgmt-sec-ssl-profile-MGMT)# certificate ca-cert.pem
  ```

### Configuration Errors

**Problem:** `Configuration validation failed`

**Solutions:**
- Run with `--dry-run --diff` to inspect configuration
- Verify configuration syntax
- Check for unsupported commands on specific EOS versions
- Review device logs:
  ```
  device# show logging last 10 minutes
  ```

### Missing Configuration Files

**Problem:** Devices are skipped with "No configuration file found"

**Solutions:**
- Verify configuration files exist in configs directory
- Check file naming: Must be `<hostname>.cfg`
- Specify custom configs path: `-c /path/to/configs`
- Generate configurations first:
  ```bash
  avd-cli generate configs -i ./inventory
  ```

### Credential Errors

**Problem:** `Missing required credentials: ansible_user, ansible_password`

**Solutions:**
- Add credentials to inventory at group or host level
- Example group-level credentials:
  ```yaml
  all:
    children:
      fabric:
        vars:
          ansible_user: admin
          ansible_password: admin123
        hosts:
          device-1:
            ansible_host: 192.168.0.10
  ```

### Concurrency Issues

**Problem:** Too many concurrent connections cause device overload

**Solutions:**
- Reduce concurrency: `--max-concurrent 5`
- Increase device timeout: `--timeout 60`
- Deploy to groups separately:
  ```bash
  avd-cli deploy eos -i ./inventory -l spines
  avd-cli deploy eos -i ./inventory -l leafs
  ```

## Best Practices

### 1. Always Dry-Run First

Before applying configurations, validate with dry-run:

```bash
avd-cli deploy eos -i ./inventory --dry-run --diff
```

Review diffs carefully before live deployment.

### 2. Use Group Filtering

Deploy to groups incrementally:

```bash
# Deploy spines first
avd-cli deploy eos -i ./inventory -l spines

# Then deploy leafs
avd-cli deploy eos -i ./inventory -l leafs
```

### 3. Version Control Configurations

Always store generated configurations in version control before deployment:

```bash
git add inventory/intended/configs/
git commit -m "feat: update spine configurations for OSPF"
git push
```

### 4. Test in Lab First

Use a lab environment before production:

```bash
# Lab deployment (SSL verification disabled)
avd-cli deploy eos -i ./lab-inventory --dry-run

# Production deployment (SSL verification enabled)
avd-cli deploy eos -i ./prod-inventory --verify-ssl
```

### 5. Monitor Deployment Progress

Use verbose mode for detailed insights:

```bash
avd-cli deploy eos -i ./inventory --verbose
```

### 6. Backup Before Deployment

Always backup configurations before major changes:

```bash
# Backup running configs (use Ansible or ANTA)
ansible-playbook backup-configs.yml -i inventory/inventory.yml

# Then deploy
avd-cli deploy eos -i ./inventory
```

### 7. Always Use Validation in Production

Use config session validation (default) for production deployments:

```bash
# Production - with validation (default)
avd-cli deploy eos -i ./inventory --dry-run --diff

# Lab only - without validation (faster)
avd-cli deploy eos -i ./lab-inventory --no-session
```

### 8. Set Appropriate Timeouts

Adjust timeouts based on network conditions:

- **Lab/Fast Network:** 10-30 seconds (default: 30)
- **Production/WAN:** 60-120 seconds
- **Large Configurations:** 120+ seconds

```bash
avd-cli deploy eos -i ./inventory --timeout 120
```

### 9. Credentials Management

**Security recommendations:**
- Use Ansible Vault for sensitive credentials
- Avoid storing passwords in plain text
- Use environment variables or encrypted inventories

**Example with Ansible Vault:**
```bash
ansible-vault encrypt_string 'admin123' --name 'ansible_password'
```

### 10. Limit Concurrency for Production

Don't overwhelm production devices:

```bash
# Conservative concurrency for production
avd-cli deploy eos -i ./prod-inventory --max-concurrent 5
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy EOS Configurations

on:
  push:
    branches: [main]
    paths:
      - 'inventory/intended/configs/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install avd-cli
        run: pip install avd-cli

      - name: Dry-run deployment
        run: |
          avd-cli deploy eos -i ./inventory --dry-run --diff
        env:
          AVD_CLI_INVENTORY_PATH: ./inventory

      - name: Deploy to production
        if: github.ref == 'refs/heads/main'
        run: |
          avd-cli deploy eos -i ./inventory --verify-ssl
        env:
          AVD_CLI_VERIFY_SSL: true
```

## See Also

- [Generate Command](./generate.md) - Generate configurations before deployment
- [Validate Command](./validate.md) - Validate inventory structure
- [AVD Documentation](https://avd.arista.com) - Arista AVD documentation
