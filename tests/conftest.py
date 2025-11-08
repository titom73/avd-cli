#!/usr/bin/env python
# coding: utf-8 -*-

"""Shared pytest fixtures and configuration for all tests.

This module contains pytest configuration and fixtures that are shared
across all test modules.
"""

from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click CLI runner for testing commands.

    Returns
    -------
    CliRunner
        Click test runner instance
    """
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for test files.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in temporary directory fixture

    Yields
    ------
    Path
        Path to temporary directory

    Notes
    -----
    The directory is automatically cleaned up after the test.
    """
    yield tmp_path


@pytest.fixture
def sample_inventory_path(tmp_path: Path) -> Path:
    """Create a minimal valid AVD inventory structure for testing.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in temporary directory fixture

    Returns
    -------
    Path
        Path to the sample inventory directory

    Notes
    -----
    Creates a minimal but valid AVD inventory structure with:
    - group_vars/FABRIC.yml
    - host_vars/spine1.yml
    - inventory.yml
    """
    inventory_dir = tmp_path / "inventory"
    inventory_dir.mkdir()

    # Create group_vars directory
    group_vars = inventory_dir / "group_vars"
    group_vars.mkdir()

    # Create minimal fabric configuration
    fabric_file = group_vars / "FABRIC.yml"
    fabric_file.write_text(
        """---
fabric_name: TEST_FABRIC
design:
  type: l3ls-evpn

spine:
  defaults:
    platform: vEOS-lab
    bgp_as: 65001
  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
"""
    )

    # Create host_vars directory
    host_vars = inventory_dir / "host_vars"
    host_vars.mkdir()

    # Create minimal host configuration
    spine1_file = host_vars / "spine1.yml"
    spine1_file.write_text(
        """---
type: spine
mgmt_interface: Management1
mgmt_gateway: 192.168.0.1
"""
    )

    # Create inventory file
    inventory_file = inventory_dir / "inventory.yml"
    inventory_file.write_text(
        """---
all:
  children:
    FABRIC:
      children:
        SPINES:
          hosts:
            spine1:
"""
    )

    return inventory_dir


@pytest.fixture
def invalid_inventory_path(tmp_path: Path) -> Path:
    """Create an invalid inventory structure for testing error handling.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in temporary directory fixture

    Returns
    -------
    Path
        Path to the invalid inventory directory
    """
    inventory_dir = tmp_path / "invalid_inventory"
    inventory_dir.mkdir()

    # Create only group_vars but with invalid YAML
    group_vars = inventory_dir / "group_vars"
    group_vars.mkdir()

    bad_yaml = group_vars / "bad.yml"
    bad_yaml.write_text("invalid: yaml: syntax:")

    return inventory_dir


@pytest.fixture
def empty_inventory_path(tmp_path: Path) -> Path:
    """Create an empty inventory directory for testing.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in temporary directory fixture

    Returns
    -------
    Path
        Path to the empty inventory directory
    """
    inventory_dir = tmp_path / "empty_inventory"
    inventory_dir.mkdir()
    return inventory_dir


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Create a temporary output directory for testing.

    Parameters
    ----------
    tmp_path : Path
        pytest's built-in temporary directory fixture

    Returns
    -------
    Path
        Path to the output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture(autouse=True)
def mock_pyavd():
    """Mock pyavd module for all tests by default.

    This fixture automatically mocks pyavd to avoid requiring
    complex AVD data structures in unit tests. Integration tests
    can override this by using their own pyavd mocks or fixtures.

    Since pyavd is imported locally inside methods, we need to mock
    it at the sys.modules level.

    Yields
    ------
    MagicMock
        Mocked pyavd module with basic return values
    """
    import sys
    from unittest.mock import MagicMock

    # Create mock module
    mock = MagicMock()

    # Setup default return values for pyavd functions
    # These return values should work with the generator's expectations
    mock.get_avd_facts.return_value = {}

    # Return appropriate structured config based on hostname
    def mock_structured_config(hostname, **kwargs):
        return {"hostname": hostname, "platform": "vEOS-lab", "type": "spine"}

    mock.get_device_structured_config.side_effect = mock_structured_config

    # Return appropriate config text based on structured_config
    def mock_config_text(structured_config):
        hostname = structured_config.get("hostname", "test-device")
        platform = structured_config.get("platform", "vEOS-lab")
        device_type = structured_config.get("type", "spine")
        return (
            f"! Configuration for {hostname}\n"
            f"! Platform: {platform}\n"
            f"! Type: {device_type}\n"
            f"! Generated by avd-cli\n"
            f"hostname {hostname}\n"
        )

    mock.get_device_config.side_effect = mock_config_text

    # Return appropriate doc text based on hostname
    def mock_doc_text(hostname, **kwargs):
        return (
            f"# Device: {hostname}\n\n"
            f"## Platform Information\n\n"
            f"**Platform:** vEOS-lab\n"
            f"**Type:** spine\n"
            f"**Management IP:** 192.168.0.10\n\n"
            f"Generated by avd-cli\n"
        )

    mock.get_device_doc.side_effect = mock_doc_text

    # Mock validation functions to return success
    mock_validation_result = MagicMock()
    mock_validation_result.failed = False
    mock_validation_result.validation_errors = []
    mock_validation_result.deprecation_warnings = []
    mock.validate_inputs.return_value = mock_validation_result
    mock.validate_structured_config.return_value = mock_validation_result

    # Mock ANTA catalog generation
    mock_catalog = MagicMock()
    mock_catalog.dump.return_value = (
        "# ANTA Catalog Generated by AVD\n"
        "anta.tests.connectivity:\n"
        "  - VerifyReachability:\n"
        "      hosts:\n"
        "        - destination: 192.168.0.1\n"
        "          source: Management0\n"
        "anta.tests.interfaces:\n"
        "  - VerifyInterfacesStatus:\n"
        "      interfaces:\n"
        "        - name: Ethernet1\n"
        "          status: up\n"
    )
    mock.get_anta_catalog.return_value = mock_catalog

    # Mock ANTA inventory generation
    mock_inventory = MagicMock()
    mock_inventory.dump.return_value = (
        "# ANTA Inventory Generated by AVD\n"
        "hosts:\n"
        "  - host: 192.168.0.10\n"
        "    name: spine01\n"
        "    tags: ['spine', 'dc1']\n"
        "  - host: 192.168.0.11\n"
        "    name: spine02\n"
        "    tags: ['spine', 'dc1']\n"
    )
    mock.get_anta_inventory.return_value = mock_inventory

    # Inject mock into sys.modules
    sys.modules["pyavd"] = mock

    yield mock

    # Cleanup
    if "pyavd" in sys.modules:
        del sys.modules["pyavd"]
