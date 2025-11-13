# Migration Guide: --limit-to-groups to --limit

## Overview

Starting with version 1.x.x, the `--limit-to-groups` option has been replaced with the more flexible `--limit` option that supports both group names and hostname patterns with wildcards.

## What Changed?

### Old Behavior (--limit-to-groups)

```bash
# Only supported exact group names
avd-cli generate all -i ./inventory -o ./output --limit-to-groups SPINES
avd-cli deploy eos -i ./inventory -l LEAFS
```

### New Behavior (--limit)

```bash
# Supports group names (backward compatible)
avd-cli generate all -i ./inventory -o ./output --limit SPINES

# NEW: Supports hostname patterns with wildcards
avd-cli generate all -i ./inventory -o ./output --limit "spine*"

# NEW: Supports exact hostnames
avd-cli generate all -i ./inventory -o ./output --limit spine-01 --limit leaf-1a

# NEW: Mix groups and patterns
avd-cli deploy eos -i ./inventory -l "spine*" -l BORDER_LEAFS
```

## Backward Compatibility

✅ **The `--limit-to-groups` option continues to work** as an alias for `--limit` to ensure backward compatibility with existing scripts and workflows.

```bash
# This still works (but is deprecated)
avd-cli generate all -i ./inventory -o ./output --limit-to-groups SPINES
```

However, we recommend updating to `--limit` for new workflows to take advantage of the enhanced filtering capabilities.

## New Filtering Capabilities

### Wildcard Patterns

The `--limit` option supports glob-style wildcards:

| Pattern | Matches | Example |
|---------|---------|---------|
| `*` | Any characters | `spine*` matches `spine-01`, `spine-02`, `spineA` |
| `?` | Single character | `leaf-?` matches `leaf-1`, `leaf-a` |
| `[...]` | Character set | `leaf-[12]a` matches `leaf-1a`, `leaf-2a` |

### Examples

```bash
# All spines
avd-cli generate configs -i ./inventory -o ./output -l "spine*"

# Specific rack devices
avd-cli generate all -i ./inventory -o ./output -l "rack1-*"

# Character ranges
avd-cli deploy eos -i ./inventory -l "spine-0[1-3]"

# Multiple patterns (OR logic)
avd-cli generate all -i ./inventory -o ./output -l "spine*" -l "leaf-1*" -l BORDER_LEAFS
```

## Matching Behavior

The `--limit` option uses **OR logic** (union) across patterns:

- A device is included if it matches **ANY** pattern
- Patterns can match either **hostname** OR **group name**
- Multiple patterns expand the selection (union, not intersection)

```bash
# Includes: all devices in SPINES group + all devices with hostnames matching "leaf-*"
avd-cli generate all -i ./inventory -o ./output -l SPINES -l "leaf-*"
```

## Environment Variables

### Old Variable

```bash
export AVD_CLI_LIMIT_TO_GROUPS="SPINES,LEAFS"
```

### New Variable

```bash
# Supports both groups and patterns
export AVD_CLI_LIMIT="spine*,LEAFS,border-01"
```

⚠️ **Note**: The old `AVD_CLI_LIMIT_TO_GROUPS` variable still works but is deprecated.

## Important: How Filtering Works

### For `generate` Commands

AVD requires **all devices** in the inventory to calculate topology facts (BGP neighbors, MLAG peers, EVPN route servers, etc.). The `--limit` option filters which **output files** are generated, but all devices remain in the inventory for context:

```bash
# spine-01 config is generated correctly even though spine-02 is not filtered
# because AVD needs spine-02 for topology context
avd-cli generate configs -i ./inventory -o ./output -l spine-01
```

**What happens:**
1. ✅ Load ALL devices from inventory
2. ✅ Calculate AVD facts using all devices (BGP peers, MLAG, etc.)
3. ✅ Generate configs/docs/tests ONLY for filtered devices

This ensures configurations are always correct, even when filtering single devices.

### For `deploy` Commands

Deployment filtering affects which devices **receive configuration pushes** via eAPI:

```bash
# Only spine-01 and spine-02 will be contacted
avd-cli deploy eos -i ./inventory -l "spine*"
```

**What happens:**
1. ✅ Load inventory and configurations
2. ✅ Filter devices by pattern
3. ✅ Deploy ONLY to filtered devices via eAPI

## Migration Checklist

- [ ] Update CLI commands to use `--limit` instead of `--limit-to-groups`
- [ ] Update environment variables from `AVD_CLI_LIMIT_TO_GROUPS` to `AVD_CLI_LIMIT`
- [ ] Update CI/CD pipelines and automation scripts
- [ ] Test wildcard patterns if needed
- [ ] Update documentation and runbooks

## Need Help?

- See [Generate Command Guide](user-guide/commands/generate.md)
- See [Deploy Command Guide](user-guide/commands/deploy.md)
- Open an issue on [GitHub](https://github.com/titom73/avd-cli/issues)
