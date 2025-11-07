# AVD CLI

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://titom73.github.io/avd-cli/)

A command-line interface for processing [Arista AVD](https://avd.arista.com/) inventories and generating configurations, documentation, and ANTA tests using pyavd.

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
avd-cli generate all --inventory ./examples/atd-inventory --output ./output

# View inventory information
avd-cli info --inventory ./examples/atd-inventory
```

## Key Features

- **🔧 Configuration Generation**: Generate EOS device configurations using pyavd
- **📚 Documentation Generation**: Create comprehensive network documentation in Markdown
- **🧪 ANTA Test Generation**: Generate ANTA test catalogs for network validation
- **🌐 Multi-Fabric Support**: Process multiple network fabrics with variable inheritance
- **⚡ Rich Terminal Experience**: Beautiful CLI with progress bars and formatted output

## Documentation

Complete documentation is available at **[titom73.github.io/avd-cli](https://titom73.github.io/avd-cli/)**

## License

This project is licensed under the **Apache License 2.0**.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

---

## 🙏 Acknowledgments

**Core Dependencies:**
- [Arista Networks](https://www.arista.com/) - AVD collection and pyavd library
- [Click](https://click.palletsprojects.com/) - Elegant CLI framework
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [pytest](https://pytest.org/) - Comprehensive testing framework
- [UV](https://github.com/astral-sh/uv) - Fast Python package management

**DevOps Principles:** This project follows the CALMS framework (Culture, Automation, Lean, Measurement, Sharing) and strives to improve the DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery).

**Community:** Special thanks to the Arista AVD community and all contributors making network automation accessible and reliable.

---

📚 **[Complete Documentation](https://titom73.github.io/avd-cli/)** | 🚀 **[Quick Start Guide](https://titom73.github.io/avd-cli/getting-started/quickstart/)** | 💡 **[Examples](examples/)**
