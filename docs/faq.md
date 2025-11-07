# Frequently Asked Questions

## Installation

**Q: How do I install AVD CLI?**

A: See the [Installation Guide](getting-started/installation.md).

## Usage

**Q: What workflows are supported?**

A: AVD CLI supports `eos-design` (full pipeline) and `cli-config` (config-only). See [Workflows](user-guide/workflows.md).

**Q: Can I use environment variables?**

A: Yes! All options support `AVD_CLI_*` environment variables. See [Environment Variables](user-guide/environment-variables.md).

## Troubleshooting

**Q: I get "command not found" after installation**

A: Ensure pipx's bin directory is in your PATH. See [Installation Troubleshooting](getting-started/installation.md#troubleshooting).

**Q: Validation fails with "No spine devices found"**

A: Ensure your fabric group_vars includes spine device definitions. See [validate Command](user-guide/commands/validate.md).
