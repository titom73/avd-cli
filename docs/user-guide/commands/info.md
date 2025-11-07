# info Command

Display detailed information about your AVD inventory.

---

## Synopsis

```bash
avd-cli info [OPTIONS]
```

---

## Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--inventory-path` | `-i` | Path | *Required* | Path to AVD inventory directory |
| `--format` | `-f` | Choice | `table` | Output format: `table`, `json`, or `yaml` |
| `--verbose` | `-v` | Flag | `false` | Enable verbose output |

---

## Usage Examples

### Table Format (Default)

```bash
avd-cli info -i ./inventory
```

**Output:**

```
→ Loading inventory...
✓ Loaded 10 devices

           Inventory Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric                  ┃ Value     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Devices           │ 10        │
│ Total Fabrics           │ 1         │
│ Fabric: CAMPUS_FABRIC   │           │
│   - Design Type         │ l3ls-evpn │
│   - Spine Devices       │ 2         │
│   - Leaf Devices        │ 8         │
└─────────────────────────┴───────────┘

                             Devices
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Hostname       ┃ Type  ┃ Platform ┃ Management IP ┃ Fabric        ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ spine01        │ spine │ 7050X3   │ 192.168.0.10  │ CAMPUS_FABRIC │
│ spine02        │ spine │ 7050X3   │ 192.168.0.11  │ CAMPUS_FABRIC │
│ leaf-1a        │ leaf  │ 722XP    │ 192.168.0.12  │ CAMPUS_FABRIC │
│ ...            │       │          │               │               │
└────────────────┴───────┴──────────┴───────────────┴───────────────┘
```

### JSON Format

```bash
avd-cli info -i ./inventory --format json
```

**Output:**

```json
{
  "summary": {
    "total_devices": 10,
    "total_fabrics": 1
  },
  "fabrics": [
    {
      "name": "CAMPUS_FABRIC",
      "design_type": "l3ls-evpn",
      "spine_count": 2,
      "leaf_count": 8,
      "devices": [
        {
          "hostname": "spine01",
          "type": "spine",
          "platform": "7050X3",
          "mgmt_ip": "192.168.0.10"
        }
      ]
    }
  ]
}
```

### YAML Format

```bash
avd-cli info -i ./inventory --format yaml
```

**Output:**

```yaml
summary:
  total_devices: 10
  total_fabrics: 1
fabrics:
  - name: CAMPUS_FABRIC
    design_type: l3ls-evpn
    spine_count: 2
    leaf_count: 8
    devices:
      - hostname: spine01
        type: spine
        platform: 7050X3
        mgmt_ip: 192.168.0.10
```

---

## Environment Variables

| CLI Option | Environment Variable | Example |
|-----------|---------------------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | `./inventory` |
| `-f, --format` | `AVD_CLI_FORMAT` | `json` |

### Example

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_FORMAT=json

avd-cli info
```

---

## Use Cases

### Quick Inventory Overview

```bash
# Get a quick summary
avd-cli info -i ./inventory
```

### Machine-Readable Output

```bash
# For scripts or CI/CD
avd-cli info -i ./inventory --format json > inventory-info.json
```

### Verbose Diagnostics

```bash
# Detailed output for troubleshooting
avd-cli info -i ./inventory --verbose
```

---

## See Also

- [validate Command](validate.md) - Validate inventory structure
- [Inventory Structure](../inventory-structure.md) - Learn about inventory organization
