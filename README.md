# AVD CLI

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful command-line interface for processing Arista AVD (Arista Validated Designs) inventories and generating configurations, documentation, and ANTA tests using py-avd.

## 🌟 Key Features

### 🎯 Core Capabilities

- **Configuration Generation**: Generate device configurations from AVD inventory using py-avd
- **Documentation Generation**: Automatically generate comprehensive network documentation
- **Multi-Fabric Support**: Process multiple network fabrics in a single inventory

### 🚀 Advanced Features

- **Jinja2 Template Support**: Full support for Jinja2 variables and expressions in inventory files
  - Use `{{ ansible_hostname }}` and other Jinja2 expressions
  - Template variables are resolved before AVD processing
  - Support for complex expressions and filters

- **Variable Inheritance**: Sophisticated variable inheritance across inventory hierarchy
  - Variables from `group_vars/all.yml` are inherited by all devices
  - Group-specific variables override global variables
  - Host-specific variables take highest precedence
  - Nested group inheritance fully supported

- **Flexible Variable Organization**: Support for both files and directories in group_vars/host_vars
  - Use single YAML files: `group_vars/SPINES.yml`
  - Or organize in directories: `group_vars/SPINES/main.yml`, `group_vars/SPINES/interfaces.yml`
  - All YAML files in a directory are automatically merged
  - Ideal for managing large, complex inventories

- **Custom Node Types**: Support for custom node types beyond standard AVD topology
  - Define custom hardware platforms
  - Support for specialized device roles
  - Flexible device type mapping

- **Group Filtering**: Process specific device groups only for faster iterations
  - Filter by spine, leaf, or custom groups
  - Multiple group selection with `-l` flag
  - Useful for testing and incremental deployments

- **Rich Terminal Output**: Beautiful and informative CLI experience
  - Color-coded status messages
  - Progress indicators for long operations
  - Formatted tables for inventory information
  - JSON and YAML output formats available

### Roadmap

- **ANTA Test Generation**: Create ANTA test files for network validation
- **Flexible Workflows**: Support for both full (eos_design + eos_cli_config_gen) and config-only workflows

## 💻 Usage

### Basic Commands

```bash
# Display help
avd-cli --help

# Generate configurations and documentation
avd-cli generate -i ./inventory -o ./output

# Generate configurations only (skip documentation)
avd-cli generate -i ./inventory -o ./output --config-only

# Generate with ANTA tests
avd-cli generate -i ./inventory -o ./output --generate-tests

# Limit to specific groups
avd-cli generate -i ./inventory -o ./output -l spine -l leaf

# Validate inventory structure
avd-cli validate -i ./inventory

# Display inventory information
avd-cli info -i ./inventory
```

### Command Options

#### `generate` - Generate configurations and documentation

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -o, --output-path PATH          Output directory for generated files [required]
  -l, --limit-to-groups TEXT      Limit processing to specific groups (multiple)
  --config-only                   Generate configuration only (skip docs)
  --workflow [full|config-only]   Workflow type [default: full]
  --generate-tests                Generate ANTA tests
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

#### `validate` - Validate inventory structure

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

#### `info` - Display inventory information

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory [required]
  -f, --format [table|json|yaml]  Output format [default: table]
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

## 📁 Inventory Structure

AVD CLI supports standard Ansible inventory structure with AVD group_vars:

```
inventory/
├── inventory.yml           # Main inventory file (hosts and groups)
├── group_vars/            # Group-level variables
│   ├── all.yml           # Global variables (inherited by all devices)
│   ├── FABRIC.yml        # Fabric-level variables
│   ├── SPINES.yml        # Spine-specific variables
│   └── LEAFS.yml         # Leaf-specific variables
└── host_vars/             # Host-level variables (optional)
    ├── spine1.yml
    └── leaf1.yml
```

### Variable Inheritance

Variables are inherited in this order (last wins):

1. `group_vars/all.yml` - Global defaults
2. Parent group variables (e.g., FABRIC)
3. Child group variables (e.g., SPINES, LEAFS)
4. Host-specific variables from `host_vars/` (if present)

### Jinja2 Template Support

You can use Jinja2 expressions in any YAML file:

```yaml
# group_vars/SPINES.yml
spine:
  platform: "{{ custom_platform | default('vEOS-lab') }}"
  nodes:
    - name: "{{ site_code }}-spine1"
      id: 1
      mgmt_ip: "{{ mgmt_subnet }}.11/24"
```

Variables are resolved before being processed by AVD.

## 🏗️ Architecture

AVD CLI follows a clean, layered architecture:

```
avd_cli/
├── cli/              # CLI interface (Click commands)
├── models/           # Data models and validation
├── logics/           # Business logic and processing
└── utils/            # Utility functions
```

For detailed information, see:
- [Architecture Specification](spec/tool-avd-cli-architecture.md)
- [Workflow Processing](spec/process-avd-workflow.md)
- [Data Schema](spec/data-avd-inventory-schema.md)
- [Testing Strategy](spec/infrastructure-testing-strategy.md)

## 📋 Requirements

- Python 3.9 or higher
- UV package manager (recommended) or pip
- Valid Arista AVD inventory structure

## 🚀 Installation

### Using UV (Recommended)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/aristanetworks/avd-cli.git
cd avd-cli

# Install the package
uv sync
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/aristanetworks/avd-cli.git
cd avd-cli

# Install the package
pip install -e .
```

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for:

- Development environment setup
- Running tests and quality checks
- Code style guidelines
- Git workflow and commit conventions
- Pull request process

Quick start for contributors:

```bash
# Setup development environment
uv sync --extra dev
make pre-commit-install

# Run all checks before committing
make check
```

See also:
- [Development Tools Guide](docs/DEVELOPMENT_TOOLS.md) - Detailed guide on Make and Tox
- [Contributing Guide](docs/CONTRIBUTING.md) - Full contribution guidelines

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Arista Networks](https://www.arista.com/) for AVD
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [pytest](https://pytest.org/) for testing framework
