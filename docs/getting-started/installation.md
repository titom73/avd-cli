# Installation

This guide will help you install AVD CLI on your system.

---

## Prerequisites

Before installing AVD CLI, ensure you have:

- **Python 3.9 or higher** installed on your system
- **pip** or **pipx** for package installation
- Basic familiarity with command-line tools

---

## Installation Methods

### Method 1: Using pipx (Recommended)

[pipx](https://pypa.github.io/pipx/) installs packages in isolated environments, preventing dependency conflicts.

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install avd-cli
pipx install git+https://github.com/titom73/avd-cli.git
```

!!! tip "Why pipx?"
    pipx creates an isolated environment for each application, avoiding conflicts with other Python packages on your system.

### Method 2: Using pip

```bash
# Install from GitHub
pip install git+https://github.com/titom73/avd-cli.git

# Or install in a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install git+https://github.com/titom73/avd-cli.git
```

### Method 3: From Source (Development)

For contributors or users who want the latest development version:

```bash
# Clone the repository
git clone https://github.com/titom73/avd-cli.git
cd avd-cli

# Install with UV (recommended for development)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras

# Or with pip
pip install -e .
```

---

## Verify Installation

After installation, verify that AVD CLI is working:

```bash
# Check version
avd-cli --version

# Display help
avd-cli --help
```

Expected output:

```
Usage: avd-cli [OPTIONS] COMMAND [ARGS]...

  AVD CLI - A powerful tool for processing Arista AVD inventories

Options:
  --version   Show the version and exit.
  --help      Show this message and exit.

Commands:
  generate  Generate configurations, documentation, or tests
  info      Display inventory information
  validate  Validate inventory structure
```

---

## Upgrading

### With pipx

```bash
pipx upgrade avd-cli
```

### With pip

```bash
pip install --upgrade git+https://github.com/titom73/avd-cli.git
```

---

## Uninstallation

### With pipx

```bash
pipx uninstall avd-cli
```

### With pip

```bash
pip uninstall avd-cli
```

---

## Dependencies

AVD CLI automatically installs the following core dependencies:

- **[Click](https://click.palletsprojects.com/)** (≥8.1.0) - CLI framework
- **[Rich](https://github.com/Textualize/rich)** (≥13.0.0) - Terminal output formatting
- **[PyYAML](https://pyyaml.org/)** (≥6.0) - YAML parsing
- **[Jinja2](https://jinja.palletsprojects.com/)** (≥3.0.0) - Template engine
- **[pyavd](https://avd.arista.com/)** (≥4.0.0) - Arista AVD library

---

## Next Steps

Now that AVD CLI is installed, you can:

- Follow the [Quick Start Guide](quickstart.md) to generate your first configuration
- Learn about [Basic Usage](basic-usage.md)
- Explore the [User Guide](../user-guide/commands/overview.md) for detailed command information

---

## Troubleshooting

### Command not found

If you get a `command not found` error after installation:

1. **With pipx**: Ensure pipx's bin directory is in your PATH:

   ```bash
   python3 -m pipx ensurepath
   # Then restart your terminal
   ```

2. **With pip**: If installed with `--user`, ensure your user's bin directory is in PATH:

   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   # Add this to your ~/.bashrc or ~/.zshrc for persistence
   ```

### Permission Errors

If you encounter permission errors:

```bash
# Use --user flag with pip
pip install --user git+https://github.com/titom73/avd-cli.git

# Or use a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/titom73/avd-cli.git
```

### Python Version Issues

Ensure you're using Python 3.9 or higher:

```bash
python3 --version
```

If your default Python is older, you may need to install a newer version or use `python3.9`, `python3.10`, etc. explicitly.

---

!!! question "Need Help?"
    If you encounter issues during installation, please:

    - Check the [FAQ](../faq.md) for common questions
    - Open an issue on [GitHub](https://github.com/titom73/avd-cli/issues)
    - Consult the [Contributing Guide](../development/contributing.md) for development setup
