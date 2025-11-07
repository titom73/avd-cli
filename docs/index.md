# AVD CLI

A command-line interface for processing Arista AVD inventories and generating configurations, documentation, and tests.

## What it does

- **Generate configurations** from AVD inventory files
- **Create documentation** automatically
- **Validate inventory** structure and data
- **Output ANTA tests** for network validation

## Quick Start

```bash
# Install avd-cli
pipx install git+https://github.com/titom73/avd-cli.git

# Generate all outputs (configs, docs, tests)
avd-cli generate all \
  --inventory-path ./inventory \
  --output-path ./output \
  --workflow eos-design

→ Loading inventory...
✓ Loaded 10 devices
→ Generating configurations, documentation, and tests...

✓ Generation complete!
                      Generated Files
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category       ┃ Count ┃ Output Path                    ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Configurations │    10 │ ./output/configs               │
│ Documentation  │    10 │ ./output/documentation         │
│ Tests          │     1 │ ./output/tests                 │
└────────────────┴───────┴────────────────────────────────┘
```

---

## 💡 Advanced Features

- **Jinja2 Template Support**: Full support for Jinja2 variables and expressions in inventory files
- **Variable Inheritance**: Sophisticated variable inheritance across inventory hierarchy
- **Flexible Variable Organization**: Support for both files and directories in group_vars/host_vars
- **Environment Variables**: All CLI options support `AVD_CLI_*` environment variables
- **Rich Terminal Output**: Beautiful and informative CLI experience with color-coded messages

---

## 📖 Documentation

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } __Getting Started__

    ---

    Installation, quick start guide, and basic usage examples

    [:octicons-arrow-right-24: Get Started](getting-started/installation.md)

-   :material-book-open-variant:{ .lg .middle } __User Guide__

    ---

    Comprehensive guide covering all commands, inventory structure, and advanced features

    [:octicons-arrow-right-24: User Guide](user-guide/commands/overview.md)

-   :material-code-braces:{ .lg .middle } __API Reference__

    ---

    Detailed API documentation for all modules and functions

    [:octicons-arrow-right-24: API Docs](api/cli/main.md)

-   :material-frequently-asked-questions:{ .lg .middle } __FAQ__

    ---

    Frequently asked questions and troubleshooting tips

    [:octicons-arrow-right-24: FAQ](faq.md)

</div>

---

## 🤝 Contributing

Contributions are welcome! Check out our [Contributing Guide](development/contributing.md) for:

- Development environment setup
- Running tests and quality checks
- Code style guidelines
- Pull request process

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/titom73/avd-cli/blob/main/LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Arista Networks](https://www.arista.com/) for AVD
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [pytest](https://pytest.org/) for testing framework
