# validate Command

Validate your AVD inventory structure before generating configurations.

---

## Synopsis

```bash
avd-cli validate [OPTIONS]
```

---

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to AVD inventory directory |
| `--verbose` | `-v` | Flag | `false` | Enable verbose validation output |

---

## What Gets Validated

The validate command performs comprehensive checks on your inventory:

### ✅ File Structure

- Inventory file exists (`inventory.yml` or `hosts.yml`)
- Required `group_vars/` directory exists
- Fabric-level group variables exist

### ✅ Topology Validation

- Fabric topology structure is valid
- Spine devices are defined (for `eos-design` workflow)
- Node groups are properly structured
- Device nodes have required properties

### ✅ Variable Validation

- Required variables are present
- Variable hierarchy is correct
- Jinja2 templates are syntactically valid

### ✅ Schema Validation

- Group variable files are valid YAML
- Device definitions follow AVD schema
- Fabric design parameters are complete

---

## Usage Examples

### Basic Validation

```bash
avd-cli validate -i ./inventory
```

**Output (Success):**

```
→ Validating inventory structure...
✓ Inventory file found: inventory.yml
✓ Group variables directory found: group_vars/
✓ Fabric group variables found: group_vars/CAMPUS_FABRIC.yml
✓ Fabric topology validated: CAMPUS_FABRIC
✓ Found 2 spine devices
✓ Found 8 leaf devices
✓ Variable hierarchy validated
✓ All device definitions are valid

✓ Validation successful!
```

**Output (Errors):**

```
→ Validating inventory structure...
✓ Inventory file found: inventory.yml
✓ Group variables directory found: group_vars/
✗ Fabric group variables not found: group_vars/CAMPUS_FABRIC.yml
✗ Spine devices not found in topology

✗ Validation failed with 2 errors
```

### Verbose Validation

```bash
avd-cli validate -i ./inventory --verbose
```

Provides detailed information about:

- File paths being checked
- Variables being loaded
- Jinja2 template resolution
- Validation steps performed

---

## Environment Variables

| CLI Option | Environment Variable | Example |
|-----------|---------------------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | `./inventory` |

### Example

```bash
export AVD_CLI_INVENTORY_PATH=./inventory

avd-cli validate
```

---

## Integration with CI/CD

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Validating AVD inventory..."
avd-cli validate -i ./inventory

if [ $? -ne 0 ]; then
    echo "❌ Inventory validation failed"
    exit 1
fi

echo "✅ Inventory validation passed"
```

### GitLab CI

```yaml
validate:
  stage: validate
  script:
    - avd-cli validate -i ./inventory
```

### GitHub Actions

```yaml
- name: Validate Inventory
  run: |
    avd-cli validate -i ./inventory
```

---

## Common Issues

### Missing Spine Devices

**Error:**

```
✗ Spine devices not found in topology
```

**Solution:**
Ensure your fabric configuration includes spine device definitions:

```yaml
# group_vars/FABRIC.yml
spine:
  nodes:
    - name: spine1
      id: 1
```

### Invalid YAML Syntax

**Error:**

```
✗ Failed to parse group_vars/FABRIC.yml: YAML syntax error
```

**Solution:**
Check YAML syntax, indentation, and special characters.

### Missing Required Variables

**Error:**

```
✗ Required variable 'fabric_name' not found
```

**Solution:**
Add the required variable to your fabric group_vars:

```yaml
# group_vars/FABRIC.yml
fabric_name: MY_FABRIC
```

---

## See Also

- [Inventory Structure](../inventory-structure.md) - Learn about inventory organization
- [generate Command](generate.md) - Generate configurations after validation
- [info Command](info.md) - View inventory information
