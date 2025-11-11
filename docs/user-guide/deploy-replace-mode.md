# Deploy REPLACE Mode

## Overview

The `avd-cli deploy eos` command uses **REPLACE mode** by default, which performs a complete configuration replacement on target devices. This mode uses EOS config sessions with `rollback clean-config` to ensure a true replace operation.

## How REPLACE Mode Works

1. **Creates a config session** on the device
2. **Applies `rollback clean-config`** - This removes ALL existing configuration
3. **Applies the new configuration** from your intended configs
4. **Validates the configuration** using EOS session validation
5. **Commits or aborts** the session based on validation results

## Critical Requirements

⚠️ **IMPORTANT**: Your configuration files must be **COMPLETE** and include all necessary sections for device management and access.

### Required Configuration Sections

Your configuration **MUST** include:

```eos
!
! Management API - Required for eAPI access
management api http-commands
   no shutdown
   !
   vrf MGMT
      no shutdown
!
! User accounts - At least one user for access
username admin privilege 15 role network-admin secret sha512 <hash>
username demo privilege 15 role network-admin secret sha512 <hash>
!
! AAA Configuration (if using authentication)
aaa authentication login default local
aaa authorization exec default local
aaa authorization commands all default local
!
```

### What Happens Without Management Config

If you deploy a configuration **without** these critical sections:

- ❌ Management API will be removed → **Loss of eAPI access**
- ❌ User accounts will be removed → **Cannot login to device**
- ❌ Device becomes **inaccessible** via eAPI

The only recovery would be through console access.

## Using with Arista AVD

By default, Arista AVD generates fabric-specific configuration but **does not include** management plane configuration. You need to ensure your AVD data models include management sections.

### Option 1: Add Management to AVD Data Model

Add management configuration to your group_vars:

```yaml
# group_vars/FABRIC.yml
management_api_http:
  enable_vrfs:
    - name: MGMT
  enable_https: true

local_users:
  - name: admin
    privilege: 15
    role: network-admin
    sha512_password: "<hash>"
  - name: cvpadmin
    privilege: 15
    role: network-admin
    sha512_password: "<hash>"
```

AVD will then include these sections in the generated configurations.

### Option 2: Post-Process Configurations

After AVD generates configurations, append management sections:

```bash
# Add management config to all device configs
for config in intended/configs/*.cfg; do
  cat << 'EOF' >> "$config"
!
management api http-commands
   no shutdown
   vrf MGMT
      no shutdown
!
username admin privilege 15 role network-admin secret sha512 $6$...
EOF
done
```

### Option 3: Use Configuration Fragments

Create a management template and merge it with AVD configs during generation.

## Deployment Workflow

### 1. Generate Complete Configuration

```bash
# Generate AVD configs with management sections included
ansible-playbook playbooks/build.yml
```

### 2. Verify Configuration Completeness

Check that your intended configs include management sections:

```bash
# Verify management API is present
grep -l "management api http-commands" intended/configs/*.cfg

# Verify users are present
grep -l "username admin" intended/configs/*.cfg
```

### 3. Preview Changes with Diff

Use `--dry-run --diff` to see what will change:

```bash
avd-cli deploy eos -i inventory.yml -l FABRIC --dry-run --diff
```

Review the diff output carefully:
- ✅ Additions shown with `+` prefix
- ✅ Deletions shown with `-` prefix
- ⚠️ Ensure management config is **not** being deleted

### 4. Deploy Configuration

Deploy to a test device first:

```bash
# Test on single device
avd-cli deploy eos -i inventory.yml --limit leaf-1a --diff
```

Then deploy to the full fabric:

```bash
# Deploy to all devices in group
avd-cli deploy eos -i inventory.yml -l FABRIC
```

## Understanding the Diff Output

The `--diff` option shows configuration differences in unified diff format:

```diff
Configuration Diffs

leaf-1a:
--- system:/running-config
+++ session:/avd_cli_1234567890-session-config
-alias old_alias show version
+alias new_alias show version
-vlan 100
-   name old_vlan
+vlan 200
+   name new_vlan
```

- Lines with `-` (red) are **being removed** from the device
- Lines with `+` (green) are **being added** to the device
- Context lines (no prefix) show surrounding configuration

## Best Practices

### 1. Always Use --dry-run First

```bash
avd-cli deploy eos -i inventory.yml -l FABRIC --dry-run --diff
```

Review the diff output before committing changes.

### 2. Test on Non-Production Devices

Deploy to lab or test environments first to validate:
- Configuration completeness
- No unexpected deletions
- Management access maintained

### 3. Maintain Configuration Templates

Keep standardized templates for:
- Management plane configuration
- Security baseline (users, AAA, SSH)
- Monitoring and logging configuration

### 4. Use Version Control

Store all configurations in Git:
```bash
git add intended/configs/
git commit -m "Update fabric configuration for deploy"
git push
```

This provides rollback capability if needed.

### 5. Monitor Deployment

Watch for errors during deployment:
- Configuration validation failures
- Session commit errors
- Connection losses (indicates management config issues)

## Troubleshooting

### "Lost access after deployment"

**Cause**: Management configuration was not included in the deployed config.

**Prevention**: Always verify management sections are present before deployment.

**Recovery**: Access device via console and restore management configuration manually.

### "Configuration validation failed"

**Cause**: Invalid configuration syntax or unsupported commands.

**Solution**: 
1. Review the error message for the specific command that failed
2. Check EOS version compatibility
3. Validate configuration with `--dry-run` first

### "Session commit timeout"

**Cause**: Large configuration taking too long to commit.

**Solution**:
1. Break deployment into smaller batches
2. Increase device timeout (if supported)
3. Check device CPU/memory utilization

## Comparison: REPLACE vs MERGE

| Aspect | REPLACE Mode (Current) | MERGE Mode (Future) |
|--------|------------------------|---------------------|
| Deletions | ✅ Automatic | ❌ Must use `no` commands |
| Config Requirements | Complete config needed | Partial config OK |
| Management Config | Must be included | Optional |
| Use Case | Full fabric builds | Incremental changes |
| Risk Level | Higher (can lose access) | Lower (additive only) |

## See Also

- [Getting Started Guide](../getting-started/quickstart.md)
- [Deploy Command Reference](./deploy-command.md)
- [Arista AVD Documentation](https://avd.arista.com/)
