# AVD CLI

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/titom73/6af809c95b2b659058da5539ddba7791/raw/avd-cli-coverage.json&cacheSeconds=300)](https://github.com/titom73/avd-cli/actions/workflows/coverage-badge.yml)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://titom73.github.io/avd-cli/)

A command-line interface for processing [Arista AVD](https://avd.arista.com/) inventories and generating configurations, documentation, and ANTA tests using pyavd.

> [!IMPORTANT]
> **Personal Project Notice**
>
> This project (`avd-cli`) is a **personal project** and is **not an official development** of the Arista AVD team or Arista Networks. It is maintained independently and is not endorsed, supported, or affiliated with Arista Networks, Inc.
>
> For official AVD tools and support, please visit [avd.arista.com](https://avd.arista.com/).

## Key Features

- **🔧 Configuration Generation**: Generate EOS device configurations using pyavd
- **📚 Documentation Generation**: Create comprehensive network documentation in Markdown
- **🧪 ANTA Test Generation**: Generate ANTA test catalogs for network validation
- **🚀 Configuration Deployment**: Deploy configurations to EOS devices via eAPI with diff statistics
- **⚡ Lightning fast generation**: Generate configurations, documentation and tests way faster than ansible (`1.28sec` for 10 hosts compare to `3sec` with Ansible)
- **🌐 Multi-Fabric Support**: Process multiple network fabrics with variable inheritance
- **🔧 Rich Terminal Experience**: Beautiful CLI with progress bars and formatted output

## Getting Started

### Installation

```bash
# Using pipx (recommended)
pipx install git+https://github.com/titom73/avd-cli.git

# Or using pip
pip install git+https://github.com/titom73/avd-cli.git
```

### Basic Usage

```bash
# Generate all outputs (configs, documentation, ANTA tests)
# Default output: ./examples/atd-inventory/intended/
avd-cli generate all --inventory-path ./examples/atd-inventory
→ Loading inventory...
✓ Loaded 10 devices
ℹ Using default output path: examples/atd-inventory/intended
→ Generating configurations, documentation, and tests...

✓ Generation complete!
                          Generated Files
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category       ┃ Count ┃ Output Path                                     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Configurations │    10 │ examples/atd-inventory/intended/configs         │
│ Documentation  │    10 │ examples/atd-inventory/intended/documentation   │
│ Tests          │     2 │ examples/atd-inventory/intended/tests           │
└────────────────┴───────┴─────────────────────────────────────────────────┘

# Deploy configurations to EOS devices
avd-cli deploy eos --inventory-path ./examples/atd-inventory --dry-run --diff

Deployment Plan (dry-run)
  Mode: replace
  Targets: 10 devices
  Concurrency: 10 devices

⠼ Deploying to 10 devices...

                      Deployment Status
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Hostname       ┃ Status  ┃ Duration ┃ Diff (+/-) ┃ Error ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│ spine01        │ success │ 2.34s    │ +127 / -5  │       │
│ spine02        │ success │ 1.89s    │ +127 / -5  │       │
│ leaf-1a        │ success │ 3.12s    │ +245 / -12 │       │
│ ...            │ ...     │ ...      │ ...        │       │
└────────────────┴─────────┴──────────┴────────────┴───────┘
```

## Documentation

Complete documentation is available at **[titom73.github.io/avd-cli](https://titom73.github.io/avd-cli/)**

## 🙏 Acknowledgments

**Core Dependencies:**

- [Arista Networks AVD](https://avd.arista.com/) - AVD collection and pyavd library
- [Arista Networks ANTA](https://anta.arista.com/) - ANTA Framewaork for network testing
- [Click](https://click.palletsprojects.com/) - Elegant CLI framework
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [pytest](https://pytest.org/) - Comprehensive testing framework
- [UV](https://github.com/astral-sh/uv) - Fast Python package management

**Community:** Special thanks to the [Arista AVD community](https://avd.arista.com) and all contributors making network automation accessible and reliable.

## License

This project is licensed under the **Apache License 2.0**.

<http://www.apache.org/licenses/LICENSE-2.0>
