#!/usr/bin/env python
# coding: utf-8 -*-

"""Constants and configuration values for AVD CLI.

This module contains all constant values used throughout the application.

Note
----
Platform names and device types are dynamically loaded from py-avd schema
via the `avd_cli.utils.schema` module. This approach maintains agility by
avoiding hardcoded values and ensures consistency with the underlying AVD
library.

Examples
--------
To access supported platforms and device types:

    >>> from avd_cli.utils.schema import get_supported_platforms, get_supported_device_types
    >>> platforms = get_supported_platforms()
    >>> device_types = get_supported_device_types()
"""

from pathlib import Path

# Application metadata
APP_NAME = "avd-cli"
APP_DESCRIPTION = "CLI tool for processing Arista AVD inventories"

# Default paths
DEFAULT_OUTPUT_DIR = Path("./output")
DEFAULT_CONFIGS_DIR = "configs"
DEFAULT_DOCS_DIR = "documentation"
DEFAULT_TESTS_DIR = "tests"

# Inventory structure
INVENTORY_GROUP_VARS_DIR = "group_vars"
INVENTORY_HOST_VARS_DIR = "host_vars"
INVENTORY_FILE = "inventory.yml"

# Workflow modes
WORKFLOW_MODE_EOS_DESIGN = "eos-design"
WORKFLOW_MODE_CLI_CONFIG = "cli-config"

# Deprecated workflow modes (for backward compatibility)
WORKFLOW_MODE_FULL = "full"  # Deprecated: use WORKFLOW_MODE_EOS_DESIGN
WORKFLOW_MODE_CONFIG_ONLY = "config-only"  # Deprecated: use WORKFLOW_MODE_CLI_CONFIG

# NOTE: Supported platforms and device types are now loaded dynamically
# from py-avd via avd_cli.utils.schema module.
# See: avd_cli.utils.schema.get_supported_platforms()
# See: avd_cli.utils.schema.get_supported_device_types()
# Reference: pyavd._eos_designs.schema

# Validation constraints
MAX_HOSTNAME_LENGTH = 63
MIN_HOSTNAME_LENGTH = 1
MAX_DEVICES_PER_FABRIC = 1000

# Performance limits
MAX_YAML_FILE_SIZE_MB = 10
VALIDATION_TIMEOUT_SECONDS = 2
PROGRESS_UPDATE_INTERVAL_MS = 100

# Output formats
OUTPUT_FORMAT_YAML = "yaml"
OUTPUT_FORMAT_JSON = "json"

# File extensions
CONFIG_FILE_EXT = ".cfg"
DOC_FILE_EXT = ".md"
TEST_FILE_EXT = ".yml"

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_ERROR = 1
EXIT_GENERATION_ERROR = 2
EXIT_FILE_SYSTEM_ERROR = 3
EXIT_WORKFLOW_ERROR = 4
EXIT_UNKNOWN_ERROR = 99


def normalize_workflow(workflow: str) -> str:
    """Normalize workflow value for backward compatibility.

    Maps deprecated workflow values to their current equivalents:
    - 'full' -> 'eos-design'
    - 'config-only' -> 'cli-config'

    Parameters
    ----------
    workflow : str
        Workflow value to normalize

    Returns
    -------
    str
        Normalized workflow value

    Examples
    --------
    >>> normalize_workflow("full")
    'eos-design'
    >>> normalize_workflow("eos-design")
    'eos-design'
    >>> normalize_workflow("config-only")
    'cli-config'
    """
    workflow_mapping = {
        WORKFLOW_MODE_FULL: WORKFLOW_MODE_EOS_DESIGN,
        WORKFLOW_MODE_CONFIG_ONLY: WORKFLOW_MODE_CLI_CONFIG,
    }
    return workflow_mapping.get(workflow, workflow)
