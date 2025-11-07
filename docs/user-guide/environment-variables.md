# Environment Variables

All AVD CLI options support environment variables with the `AVD_CLI_` prefix.

## Complete Reference

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | Path | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | Path | `./output` |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | Comma-separated | `SPINES,LEAFS` |
| `--workflow` | `AVD_CLI_WORKFLOW` | Choice | `eos-design` or `cli-config` |
| `--format` | `AVD_CLI_FORMAT` | Choice | `table`, `json`, `yaml` |

See [Basic Usage](../getting-started/basic-usage.md#environment-variables) for examples.
