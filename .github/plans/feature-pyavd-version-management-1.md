---
goal: Add pyavd version display and management capabilities to avd-cli
version: 1.0
date_created: 2026-01-13
last_updated: 2026-01-13
owner: titom73
status: 'Completed'
tags: ['feature', 'cli', 'pyavd', 'dependency-management']
---

# Introduction

![Status: Completed](https://img.shields.io/badge/status-Completed-green)

This plan adds pyavd version management capabilities to avd-cli:

1. **Enhanced version display**: Show both avd-cli and pyavd versions when running `avd-cli --version`
2. **Version management command**: New `avd-cli pyavd` command group to install/upgrade/downgrade pyavd to a specific version

## 1. Requirements & Constraints

- **REQ-001**: Display avd-cli version AND pyavd version when user runs `avd-cli --version`
- **REQ-002**: Provide a CLI command to install a specific pyavd version (e.g., `avd-cli pyavd install 5.6.0`)
- **REQ-003**: Support both upgrade and downgrade operations for pyavd
- **REQ-004**: User is responsible for selecting a pyavd version compatible with their Python version
- **REQ-005**: Command must work with pip/uv package managers
- **SEC-001**: Do not execute arbitrary shell commands; use Python subprocess with explicit arguments to prevent command injection
- **CON-001**: pyavd version must be dynamically retrieved at runtime (not hardcoded)
- **CON-002**: Installation command should detect the current package manager (pip vs uv) or allow user override
- **GUD-001**: Follow existing CLI patterns using Click framework and Rich console output
- **GUD-002**: Provide clear user feedback during installation process
- **PAT-001**: Use existing `avd_cli.cli.shared.console` for output formatting

## 2. Implementation Steps

### Implementation Phase 1: Enhanced Version Display

- GOAL-001: Modify `--version` output to include pyavd version alongside avd-cli version

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create utility function `get_pyavd_version()` in `avd_cli/utils/version.py` that imports pyavd and returns its `__version__` | ✅ | 2026-01-13 |
| TASK-002 | Create custom version callback function in `avd_cli/cli/main.py` that displays both versions in formatted output | ✅ | 2026-01-13 |
| TASK-003 | Replace `@click.version_option()` decorator with custom `--version` option using the new callback | ✅ | 2026-01-13 |
| TASK-004 | Add unit tests for `get_pyavd_version()` in `tests/unit/utils/test_version.py` | ✅ | 2026-01-13 |
| TASK-005 | Add CLI tests for `--version` output validation in `tests/unit/cli/test_pyavd_command.py` | ✅ | 2026-01-13 |

### Implementation Phase 2: pyavd Version Management Command

- GOAL-002: Implement `avd-cli pyavd install <version>` command to install/upgrade/downgrade pyavd

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Create `avd_cli/cli/commands/pyavd.py` with `pyavd` command group | ✅ | 2026-01-13 |
| TASK-007 | Implement `install` subcommand accepting version argument (e.g., `5.6.0`, `5.7.2`) | ✅ | 2026-01-13 |
| TASK-008 | Create `avd_cli/utils/package_manager.py` with `PackageManager` class to detect and execute pip/uv commands | ✅ | 2026-01-13 |
| TASK-009 | Implement `PackageManager.install_package(name, version)` method using `subprocess.run()` with explicit arguments | ✅ | 2026-01-13 |
| TASK-010 | Implement `PackageManager.detect_manager()` to auto-detect pip vs uv based on environment | ✅ | 2026-01-13 |
| TASK-011 | Add `--package-manager` option to `install` command to override auto-detection (`pip`, `uv`, `auto`) | ✅ | 2026-01-13 |
| TASK-012 | Add `--dry-run` option to show command without executing | ✅ | 2026-01-13 |
| TASK-013 | Register `pyavd` command group in `avd_cli/cli/main.py` | ✅ | 2026-01-13 |
| TASK-014 | Add unit tests for `PackageManager` class in `tests/unit/utils/test_package_manager.py` | ✅ | 2026-01-13 |
| TASK-015 | Add CLI tests for `pyavd install` command in `tests/unit/cli/test_pyavd_command.py` | ✅ | 2026-01-13 |

### Implementation Phase 3: Documentation and Polish

- GOAL-003: Update documentation and ensure consistent user experience

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-016 | Create `docs/user-guide/commands/pyavd.md` with pyavd version management documentation | ✅ | 2026-01-13 |
| TASK-017 | Update `docs/user-guide/commands/overview.md` to add pyavd command in command table and mermaid diagram | ✅ | 2026-01-13 |
| TASK-018 | Update `mkdocs.yml` nav section to include new pyavd command documentation page | ✅ | 2026-01-13 |
| TASK-019 | Update `README.md` with new command synopsis and pyavd version management section | ✅ | 2026-01-13 |
| TASK-020 | Add usage examples in `docs/examples/` for version management workflows (optional) | ⏭️ | Skipped |

## 3. Alternatives

- **ALT-001**: Use `pip` directly via `os.system()` – Rejected due to security concerns (shell injection risk) and lack of cross-platform reliability
- **ALT-002**: Implement version management as external shell script – Rejected to maintain single-tool user experience and cross-platform compatibility
- **ALT-003**: Only support pip, not uv – Rejected because project already uses uv and many users prefer it
- **ALT-004**: Fetch available versions from PyPI API before install – Considered but deferred; user is responsible for version selection per REQ-004

## 4. Dependencies

- **DEP-001**: `subprocess` module (Python stdlib) – For executing pip/uv commands safely
- **DEP-002**: `shutil.which()` (Python stdlib) – For detecting available package managers
- **DEP-003**: `pyavd` package – Target package for version management; `__version__` attribute required

## 5. Files

- **FILE-001**: `avd_cli/utils/version.py` – New file containing `get_pyavd_version()` utility function
- **FILE-002**: `avd_cli/utils/package_manager.py` – New file containing `PackageManager` class for pip/uv operations
- **FILE-003**: `avd_cli/cli/main.py` – Modify `--version` option and register new command group
- **FILE-004**: `avd_cli/cli/commands/pyavd.py` – New file containing `pyavd` command group and `install` subcommand
- **FILE-005**: `avd_cli/cli/commands/__init__.py` – Update to export new command
- **FILE-006**: `tests/unit/utils/test_version.py` – New test file for version utility
- **FILE-007**: `tests/unit/utils/test_package_manager.py` – New test file for package manager utility
- **FILE-008**: `tests/unit/cli/test_pyavd_command.py` – New test file for pyavd CLI command
- **FILE-009**: `docs/user-guide/commands/pyavd.md` – New documentation page for pyavd command
- **FILE-010**: `docs/user-guide/commands/overview.md` – Update command table and mermaid diagram
- **FILE-011**: `mkdocs.yml` – Update nav section to include pyavd documentation
- **FILE-012**: `README.md` – Update with pyavd version management synopsis

## 5.1 Documentation Content Specifications

### FILE-009: `docs/user-guide/commands/pyavd.md`

Documentation page structure:

1. **Title**: "pyavd Version Management"
2. **Introduction**: Description of the `avd-cli pyavd` command group
3. **Commands section**:
   - `version` subcommand with example output
   - `install` subcommand with arguments table, options table, and examples
4. **Version Display section**: Explain `avd-cli --version` dual output
5. **Package Manager Detection section**: Explain auto-detection logic (uv-managed → uv add, uv available → uv pip install, fallback → pip install)

### FILE-010: Update `docs/user-guide/commands/overview.md`

Add to command table:

| Command | Description | Learn More |
|---------|-------------|------------|
| **pyavd** | Manage pyavd package version | [Details](pyavd.md) |

Update mermaid diagram to add `pyavd` node with `version` and `install` subcommands.

### FILE-011: Update `mkdocs.yml`

Add navigation entry under User Guide section:

    - Manage pyavd Version: user-guide/commands/pyavd.md

## 6. Testing

### 6.1 Test Files Structure

| Test File | Target Module | Markers |
|-----------|---------------|---------|
| `tests/unit/utils/test_version.py` | `avd_cli/utils/version.py` | `@pytest.mark.unit` |
| `tests/unit/utils/test_package_manager.py` | `avd_cli/utils/package_manager.py` | `@pytest.mark.unit` |
| `tests/unit/cli/test_pyavd_command.py` | `avd_cli/cli/commands/pyavd.py` | `@pytest.mark.unit` |
| `tests/unit/cli/test_main_version.py` | `avd_cli/cli/main.py` (version callback) | `@pytest.mark.unit` |

### 6.2 Unit Tests for `avd_cli/utils/version.py`

- **TEST-001**: `test_get_pyavd_version_returns_valid_semver` – Verify `get_pyavd_version()` returns a string matching semver pattern (e.g., `5.7.2`)
- **TEST-002**: `test_get_pyavd_version_handles_import_error` – Mock `import pyavd` to raise `ImportError`, verify returns `"not installed"`
- **TEST-003**: `test_get_pyavd_version_handles_missing_attribute` – Mock pyavd without `__version__`, verify returns `"unknown"`

### 6.3 Unit Tests for `avd_cli/utils/package_manager.py`

- **TEST-004**: `test_detect_manager_returns_uv_when_available` – Mock `shutil.which("uv")` to return path, verify returns `"uv"`
- **TEST-005**: `test_detect_manager_returns_pip_when_uv_unavailable` – Mock `shutil.which("uv")` to return `None`, `shutil.which("pip")` returns path, verify returns `"pip"`
- **TEST-006**: `test_detect_manager_raises_when_none_available` – Mock both `shutil.which` calls to return `None`, verify raises `RuntimeError`
- **TEST-007**: `test_install_package_constructs_pip_command` – Verify `install_package("pyavd", "5.7.0", manager="pip")` builds `["pip", "install", "pyavd==5.7.0"]`
- **TEST-008**: `test_install_package_constructs_uv_command` – Verify `install_package("pyavd", "5.7.0", manager="uv")` builds `["uv", "pip", "install", "pyavd==5.7.0"]`
- **TEST-009**: `test_install_package_executes_subprocess` – Mock `subprocess.run`, verify it is called with correct arguments and `check=True`
- **TEST-010**: `test_install_package_raises_on_subprocess_error` – Mock `subprocess.run` to raise `CalledProcessError`, verify proper exception handling

### 6.4 Unit Tests for CLI Commands

- **TEST-011**: `test_version_output_contains_avd_cli_version` – Use `CliRunner`, invoke `--version`, verify output contains `avd-cli` and version number
- **TEST-012**: `test_version_output_contains_pyavd_version` – Use `CliRunner`, invoke `--version`, verify output contains `pyavd` and version number
- **TEST-013**: `test_pyavd_install_command_exists` – Use `CliRunner`, verify `avd-cli pyavd install --help` returns exit code 0
- **TEST-014**: `test_pyavd_install_requires_version_argument` – Use `CliRunner`, invoke `avd-cli pyavd install` without version, verify exit code 2 (missing argument)
- **TEST-015**: `test_pyavd_install_executes_with_valid_version` – Mock `PackageManager.install_package`, invoke `avd-cli pyavd install 5.7.0`, verify mock called with correct args
- **TEST-016**: `test_pyavd_install_dry_run_does_not_execute` – Invoke `avd-cli pyavd install 5.7.0 --dry-run`, verify `subprocess.run` not called, command printed to output
- **TEST-017**: `test_pyavd_install_package_manager_override_pip` – Invoke with `--package-manager pip`, verify pip is used regardless of detection
- **TEST-018**: `test_pyavd_install_package_manager_override_uv` – Invoke with `--package-manager uv`, verify uv is used regardless of detection
- **TEST-019**: `test_pyavd_install_displays_success_message` – Mock successful install, verify Rich console output contains success indicator
- **TEST-020**: `test_pyavd_install_displays_error_on_failure` – Mock failed install, verify error message displayed and exit code non-zero

### 6.5 Pytest Fixtures Required

**In `tests/unit/utils/test_package_manager.py`:**

- `mock_subprocess_run(mocker)` – Mock subprocess.run for safe testing without actual package installation
- `mock_shutil_which(mocker)` – Mock shutil.which for package manager detection tests

**In `tests/unit/cli/test_pyavd_command.py`:**

- `cli_runner()` – Click CliRunner for testing CLI commands
- `mock_package_manager(mocker)` – Mock PackageManager class to prevent actual package operations

### 6.6 Integration Tests (Optional)

- **TEST-INT-001**: Integration test in `tests/integration/test_pyavd_version.py` – Full CLI flow with mocked subprocess, verify end-to-end behavior

## 7. Risks & Assumptions

- **RISK-001**: User may install pyavd version incompatible with their Python version – Mitigation: Document Python compatibility in help text; user assumes responsibility per REQ-004
- **RISK-002**: Package manager detection may fail in unusual environments – Mitigation: Provide `--package-manager` override option
- **RISK-003**: Subprocess execution may fail due to permissions – Mitigation: Catch exceptions and provide clear error messages with troubleshooting hints
- **ASSUMPTION-001**: pyavd package exposes `__version__` attribute at module level
- **ASSUMPTION-002**: User has pip or uv available in PATH
- **ASSUMPTION-003**: User has write permissions to site-packages (or uses virtual environment)

## 8. Related Specifications / Further Reading

- [Click documentation - Commands and Groups](https://click.palletsprojects.com/en/8.1.x/commands/)
- [pyavd releases on PyPI](https://pypi.org/project/pyavd/#history)
- [Python subprocess security best practices](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [avd-cli existing CLI architecture](spec/tool-avd-cli-architecture.md)
