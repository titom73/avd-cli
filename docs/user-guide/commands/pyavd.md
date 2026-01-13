# pyavd Version Management

The `avd-cli pyavd` command group provides tools to manage your pyavd package version.

---

## Commands

### version

Display the currently installed pyavd version.

```bash
avd-cli pyavd version
```

**Example output:**

```
pyavd version: 5.7.2
```

---

### install

Install a specific version of pyavd.

```bash
avd-cli pyavd install <VERSION> [OPTIONS]
```

**Arguments:**

| Argument | Description | Required |
|----------|-------------|----------|
| `VERSION` | The pyavd version to install (e.g., `5.7.0`, `5.6.2`) | Yes |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--package-manager` | Package manager to use (`auto`, `pip`, `uv`) | `auto` |
| `--dry-run` | Show command without executing | `False` |

**Examples:**

```bash
# Install a specific version
avd-cli pyavd install 5.7.0

# Use pip explicitly
avd-cli pyavd install 5.7.0 --package-manager pip

# Preview the command without executing
avd-cli pyavd install 5.7.0 --dry-run
```

---

## Version Display

The `avd-cli --version` command displays both the avd-cli version and the installed pyavd version:

```bash
avd-cli --version
```

**Example output:**

```
avd-cli, version 0.2.1
pyavd, version 5.7.2
```

---

## Package Manager Detection

When using `--package-manager auto` (default), avd-cli automatically detects:

1. **uv-managed projects**: If `uv.lock` exists, uses `uv add` to update `pyproject.toml` and lock file
2. **uv available**: Uses `uv pip install` for non-managed environments
3. **pip fallback**: Uses `pip install` if uv is not available

!!! tip "For uv-managed projects"
    In projects with a `uv.lock` file, the install command uses `uv add` to ensure
    the version is properly recorded in `pyproject.toml` and persists across `uv sync`.

---

## Use Cases

### Downgrade for Compatibility

If you need to use an older pyavd version for compatibility with existing configurations:

```bash
avd-cli pyavd install 5.6.0
```

### Upgrade to Latest

To upgrade to a specific newer version:

```bash
avd-cli pyavd install 5.7.2
```

### Check Before Install

Use `--dry-run` to see what command would be executed:

```bash
avd-cli pyavd install 5.7.0 --dry-run
# Output: Dry run mode - command that would be executed:
#   uv add pyavd==5.7.0
```

---

## Next Steps

- Check [pyavd releases on PyPI](https://pypi.org/project/pyavd/#history) for available versions
- Learn about the [generate command](generate.md) to create configurations
- Learn about the [deploy command](deploy.md) to deploy to devices
