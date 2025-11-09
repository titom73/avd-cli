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
avd-cli generate all --inventory-path ./examples/atd-inventory --output ./output
→ Loading inventory...
✓ Loaded 10 devices
→ Generating configurations, documentation, and tests...

✓ Generation complete!
                     Generated Files
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category       ┃ Count ┃ Output Path                   ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Configurations │    10 │ examples/output/configs       │
│ Documentation  │    10 │ examples/output/documentation │
│ Tests          │     2 │ examples/output/tests         │
└────────────────┴───────┴───────────────────────────────┘

# View inventory information
avd-cli info --inventory-path ./examples/atd-inventory
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
