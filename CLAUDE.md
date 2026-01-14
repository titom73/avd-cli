# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AVD CLI is a Python CLI tool for processing Arista AVD inventories. It generates EOS device configurations, documentation, and ANTA tests using pyavd, and can deploy configurations via eAPI.

## Essential Commands

```bash
# Development setup
make dev-install           # Install with dev dependencies
make pre-commit-install    # Install pre-commit hooks
make git-hooks-install     # Install pre-push hook (enforces make ci)

# Running the CLI
make run ARGS="--help"     # Execute CLI with arguments
uv run avd-cli generate all --inventory-path ./examples/atd-inventory

# Testing
make test                  # All tests (must pass with >80% coverage)
make test-unit            # Unit tests only
uv run pytest tests/unit/test_loader.py -v                    # Single test file
uv run pytest tests/unit/test_loader.py::test_function -v     # Single test

# Code quality (MUST pass before pushing)
make ci                    # Full CI pipeline (lint + type + test)
make lint                  # Flake8 + Pylint (score >=9.0)
make type                  # MyPy strict mode
make format                # Black + isort auto-formatting

# Documentation
make docs-serve            # Local MkDocs server with live reload
```

## Architecture

```
avd_cli/
├── cli/                   # Click commands and terminal output
│   ├── main.py           # Entry point, shared options
│   └── commands/         # Command modules (generate, deploy, info, pyavd)
├── models/               # Data classes (DeviceDefinition, InventoryData, Fabric)
│   └── inventory.py      # Core domain models
├── logics/               # Pure business logic (no CLI dependencies)
│   ├── generator.py      # Config/docs/tests generation via pyavd
│   ├── loader.py         # Inventory parsing and variable resolution
│   ├── deployer.py       # Async eAPI deployment
│   ├── anta_generator.py # ANTA test catalog generation
│   └── topology.py       # Containerlab topology generation
├── utils/                # Shared utilities
│   ├── device_filter.py  # Glob-based device filtering
│   ├── eapi_client.py    # Arista eAPI async client
│   └── package_manager.py # PyAVD version management
├── exceptions.py         # Custom exception hierarchy (AvdCliError base)
└── constants.py          # Application constants
```

**Key patterns:**
- CLI layer uses Click decorators with Rich console output
- Logic layer imports pyavd lazily to avoid startup overhead
- Device filtering is decoupled via `DeviceFilter.from_patterns()`
- Async deployment with asyncio for concurrent device configuration
- All CLI options support environment variables (AVD_CLI_ prefix)

## Code Standards

- **Python 3.10+** required (features up to 3.10 only)
- **Type hints** on all function signatures (MyPy strict mode)
- **NumPy-style docstrings** for public functions/classes
- **Line length**: 120 characters (Black formatted)
- **Test markers**: `@pytest.mark.unit`, `.integration`, `.e2e`, `.slow`, `.asyncio`

## Exception Hierarchy

All exceptions inherit from `AvdCliError`:
- `InvalidInventoryError` - Invalid AVD inventory structure
- `ConfigurationGenerationError` - Config generation failures
- `DeploymentError` - eAPI deployment failures
- `CredentialError` - Missing ansible_user/ansible_password
- `ConnectionError` / `AuthenticationError` - Device connectivity

## Workflow Support

The tool supports two AVD workflows:
1. **eos_design + eos_cli_config_gen** - Full fabric design with structured_config
2. **eos_cli_config_gen only** - Direct CLI configuration generation

Variable resolution follows AVD precedence: device vars > group vars > fabric vars.
