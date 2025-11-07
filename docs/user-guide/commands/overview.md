# Commands Overview

AVD CLI provides a comprehensive set of commands for managing your Arista AVD network configurations.

---

## Available Commands

| Command | Description | Learn More |
|---------|-------------|------------|
| **generate** | Generate configurations, documentation, and tests | [Details](generate.md) |
| **info** | Display inventory information | [Details](info.md) |
| **validate** | Validate inventory structure | [Details](validate.md) |

---

## Command Hierarchy

```mermaid
graph LR
    A[avd-cli] --> B[generate]
    A --> C[info]
    A --> D[validate]
    B --> E[all]
    B --> F[configs]
    B --> G[docs]
    B --> H[tests]
```

---

## Common Patterns

### Using with Environment Variables

```bash
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_OUTPUT_PATH=./output

avd-cli generate all
avd-cli info
avd-cli validate
```

### Using with Explicit Options

```bash
avd-cli generate all -i ./inventory -o ./output
avd-cli info -i ./inventory
avd-cli validate -i ./inventory
```

---

## Next Steps

- Learn about the [generate command](generate.md)
- Learn about the [info command](info.md)
- Learn about the [validate command](validate.md)
