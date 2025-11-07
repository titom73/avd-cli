# AVD CLI

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful command-line interface for processing [Arista AVD (Architect, Validate, Deploy)](https://avd.arista.com/) inventories and generating configurations, documentation, and ANTA tests using py-avd.

## 🌟 Key Features

### 🎯 Core Capabilities

- **Configuration Generation**: Generate device configurations from AVD inventory using py-avd
- **Documentation Generation**: Automatically generate comprehensive network documentation
- **Multi-Fabric Support**: Process multiple network fabrics in a single inventory

## 🚀 Getting Started

### Installation

Install AVD CLI using pipx for isolated environment:

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install avd-cli
pipx install git+https://github.com/titom73/avd-cli.git
```

### Example Usage

```bash
# Generate configurations from your AVD inventory
avd-cli generate all -i examples/atd-inventory/ -o examples/outputs
→ Loading inventory...
✓ Loaded 10 devices
→ Generating configurations, documentation, and tests...

✓ Generation complete!
                      Generated Files
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category       ┃ Count ┃ Output Path                    ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Configurations │    10 │ examples/outputs/configs       │
│ Documentation  │    10 │ examples/outputs/documentation │
│ Tests          │     1 │ examples/outputs/tests         │
└────────────────┴───────┴────────────────────────────────┘

# View inventory information
avd-cli info -i examples/atd-inventory/
→ Loading inventory...
✓ Loaded 10 devices

           Inventory Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric                  ┃ Value     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Devices           │ 10        │
│ Total Fabrics           │ 1         │
│ Fabric: campus_avd      │           │
│   - Design Type         │ l3ls-evpn │
│   - Spine Devices       │ 2         │
│   - Leaf Devices        │ 8         │
│   - Border Leaf Devices │ 0         │
└─────────────────────────┴───────────┘


                             Devices
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Hostname       ┃ Type  ┃ Platform ┃ Management IP ┃ Fabric     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ leaf-1a        │ leaf  │ 722XP    │ 192.168.0.14  │ campus_avd │
│ leaf-1b        │ leaf  │ 722XP    │ 192.168.0.15  │ campus_avd │
│ leaf-2a        │ leaf  │ 722XP    │ 192.168.0.16  │ campus_avd │
│ leaf-3a        │ leaf  │ 720XP    │ 192.168.0.17  │ campus_avd │
│ leaf-3b        │ leaf  │ 720XP    │ 192.168.0.18  │ campus_avd │
│ member-leaf-3c │ leaf  │ 720XP    │ 192.168.0.19  │ campus_avd │
│ member-leaf-3d │ leaf  │ 720XP    │ 192.168.0.20  │ campus_avd │
│ member-leaf-3e │ leaf  │ 720XP    │ 192.168.0.21  │ campus_avd │
│ spine01        │ spine │ 7050X3   │ 192.168.0.12  │ campus_avd │
│ spine02        │ spine │ 7050X3   │ 192.168.0.13  │ campus_avd │
└────────────────┴───────┴──────────┴───────────────┴────────────┘
```

## 🚀 Advanced Features

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
- **Flexible Workflows**: Support for both eos-design (eos_design + eos_cli_config_gen) and cli-config (eos_cli_config_gen only) workflows

## 💻 Usage

### Basic Commands

```bash
# Display help
avd-cli --help

# Generate all outputs (configs, docs, tests)
avd-cli generate all -i ./inventory -o ./output

# Generate configurations only
avd-cli generate configs -i ./inventory -o ./output

# Generate documentation only
avd-cli generate docs -i ./inventory -o ./output

# Generate ANTA tests only
avd-cli generate tests -i ./inventory -o ./output

# Limit to specific groups
avd-cli generate all -i ./inventory -o ./output -l spine -l leaf

# Validate inventory structure
avd-cli validate -i ./inventory

# Display inventory information
avd-cli info -i ./inventory
```

### Environment Variables

All CLI options support environment variables with the `AVD_CLI_` prefix. This is useful for CI/CD pipelines and containerized environments.

```bash
# Set environment variables
export AVD_CLI_INVENTORY_PATH=./inventory
export AVD_CLI_OUTPUT_PATH=./output
export AVD_CLI_WORKFLOW=eos-design

# Run command without explicit arguments
avd-cli generate configs

# Override environment variable with CLI argument
avd-cli generate configs -o ./custom-output

# Multiple groups via environment variable (comma-separated)
export AVD_CLI_LIMIT_TO_GROUPS=spine,leaf,border
avd-cli generate all

# Boolean flags via environment variable
export AVD_CLI_SHOW_DEPRECATION_WARNINGS=true
avd-cli generate configs

# Format selection for info command
export AVD_CLI_FORMAT=json
avd-cli info
```

**Environment Variable Reference:**

| CLI Option | Environment Variable | Type | Example |
|-----------|---------------------|------|---------|
| `-i, --inventory-path` | `AVD_CLI_INVENTORY_PATH` | Path | `./inventory` |
| `-o, --output-path` | `AVD_CLI_OUTPUT_PATH` | Path | `./output` |
| `-l, --limit-to-groups` | `AVD_CLI_LIMIT_TO_GROUPS` | Comma-separated | `spine,leaf` |
| `--workflow` | `AVD_CLI_WORKFLOW` | Choice | `eos-design` or `cli-config` (legacy: `full`, `config-only`) |
| `--show-deprecation-warnings` | `AVD_CLI_SHOW_DEPRECATION_WARNINGS` | Boolean | `true`, `false`, `1`, `0` |
| `--test-type` | `AVD_CLI_TEST_TYPE` | Choice | `anta` or `robot` |
| `-f, --format` | `AVD_CLI_FORMAT` | Choice | `table`, `json`, `yaml` |

**Priority Order:** CLI arguments > Environment variables > Default values

### Command Options

#### `generate all` - Generate all outputs

```bash
Options:
  -i, --inventory-path PATH             Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -o, --output-path PATH                Output directory for generated files  [env var: AVD_CLI_OUTPUT_PATH; required]
  -l, --limit-to-groups TEXT            Limit processing to specific groups  [env var: AVD_CLI_LIMIT_TO_GROUPS]
  --workflow [eos-design|cli-config]    Workflow type  [env var: AVD_CLI_WORKFLOW; default: eos-design]
  --show-deprecation-warnings           Show pyavd warnings  [env var: AVD_CLI_SHOW_DEPRECATION_WARNINGS]
  --help                                Show help message
```

#### `generate configs` - Generate configurations only

```bash
Options:
  -i, --inventory-path PATH             Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -o, --output-path PATH                Output directory  [env var: AVD_CLI_OUTPUT_PATH; required]
  -l, --limit-to-groups TEXT            Limit to specific groups  [env var: AVD_CLI_LIMIT_TO_GROUPS]
  --workflow [eos-design|cli-config]    Workflow type  [env var: AVD_CLI_WORKFLOW; default: eos-design]
  --help                                Show help message
```

#### `generate docs` - Generate documentation only

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -o, --output-path PATH          Output directory  [env var: AVD_CLI_OUTPUT_PATH; required]
  -l, --limit-to-groups TEXT      Limit to specific groups  [env var: AVD_CLI_LIMIT_TO_GROUPS]
  --help                          Show help message
```

#### `generate tests` - Generate test files

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -o, --output-path PATH          Output directory  [env var: AVD_CLI_OUTPUT_PATH; required]
  -l, --limit-to-groups TEXT      Limit to specific groups  [env var: AVD_CLI_LIMIT_TO_GROUPS]
  --test-type [anta|robot]        Test type  [env var: AVD_CLI_TEST_TYPE; default: anta]
  --help                          Show help message
```

#### `validate` - Validate inventory structure

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -v, --verbose                   Enable verbose output
  --help                          Show help message
```

#### `info` - Display inventory information

```bash
Options:
  -i, --inventory-path PATH       Path to AVD inventory directory  [env var: AVD_CLI_INVENTORY_PATH; required]
  -f, --format [table|json|yaml]  Output format  [env var: AVD_CLI_FORMAT; default: table]
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
