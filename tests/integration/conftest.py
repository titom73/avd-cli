#!/usr/bin/env python
# coding: utf-8 -*-

"""
Pytest configuration and fixtures for integration tests.

This module provides shared fixtures and configuration for integration tests,
following the patterns defined in the infrastructure testing strategy.
"""

import os
import shutil
import tempfile
import pytest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

# Import application modules for testing
from avd_cli.logics.loader import InventoryLoader
from avd_cli.logics.generator import ConfigurationGenerator


@pytest.fixture(scope="session")
def integration_temp_dir():
    """
    Session-scoped temporary directory for integration tests.

    This fixture creates a temporary directory that persists for the entire
    test session, useful for expensive setup operations that can be shared
    across multiple test classes and methods.
    """
    temp_dir = tempfile.mkdtemp(prefix="avd_cli_integration_session_")
    temp_path = Path(temp_dir)

    yield temp_path

    # Cleanup at end of session
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def integration_workspace():
    """
    Function-scoped workspace for individual integration tests.

    Each test gets a fresh, isolated workspace directory to prevent
    test contamination and ensure reproducible results.
    """
    temp_dir = tempfile.mkdtemp(prefix="avd_cli_integration_test_")
    workspace = Path(temp_dir)

    yield workspace

    # Cleanup after each test
    if workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture(scope="function")
def minimal_inventory_structure(integration_workspace: Path) -> Path:
    """
    Create a minimal but valid AVD inventory structure for testing.

    This fixture creates the basic directory structure and files needed
    for a valid AVD inventory, suitable for integration testing.

    Returns:
        Path: Path to the inventory directory
    """
    inventory_dir = integration_workspace / "inventory"
    inventory_dir.mkdir(parents=True)

    # Create hosts.yml with minimal structure
    hosts_content = """---
all:
  children:
    AVD_FABRIC:
      children:
        AVD_SPINES:
          hosts:
            spine-01:
              ansible_host: 192.168.1.10
        AVD_LEAFS:
          hosts:
            leaf-01:
              ansible_host: 192.168.1.20
"""
    (inventory_dir / "hosts.yml").write_text(hosts_content.strip())

    # Create group_vars structure
    group_vars = inventory_dir / "group_vars"
    group_vars.mkdir()

    # AVD_FABRIC vars
    fabric_dir = group_vars / "AVD_FABRIC"
    fabric_dir.mkdir()
    fabric_content = """---
fabric_name: INTEGRATION_TEST_FABRIC
design:
  type: l3ls-evpn
"""
    (fabric_dir / "avd.yml").write_text(fabric_content.strip())

    # AVD_SPINES vars
    spine_dir = group_vars / "AVD_SPINES"
    spine_dir.mkdir()
    spine_content = """---
type: spine
platform: cEOS-lab
"""
    (spine_dir / "avd.yml").write_text(spine_content.strip())

    # AVD_LEAFS vars
    leaf_dir = group_vars / "AVD_LEAFS"
    leaf_dir.mkdir()
    leaf_content = """---
type: leaf
platform: cEOS-lab
"""
    (leaf_dir / "avd.yml").write_text(leaf_content.strip())

    return inventory_dir


@pytest.fixture(scope="function")
def extended_inventory_structure(integration_workspace: Path) -> Path:
    """
    Create an extended AVD inventory structure with more devices and groups.

    This fixture creates a more complex inventory suitable for testing
    advanced scenarios like group filtering, multiple device types, etc.

    Returns:
        Path: Path to the inventory directory
    """
    inventory_dir = integration_workspace / "inventory"
    inventory_dir.mkdir(parents=True)

    # Create comprehensive hosts.yml
    hosts_content = """---
all:
  children:
    AVD_FABRIC:
      children:
        AVD_SPINES:
          hosts:
            spine-01:
              ansible_host: 192.168.1.10
            spine-02:
              ansible_host: 192.168.1.11
        AVD_LEAFS:
          hosts:
            leaf-01:
              ansible_host: 192.168.1.20
            leaf-02:
              ansible_host: 192.168.1.21
            leaf-03:
              ansible_host: 192.168.1.22
        AVD_BORDER_LEAFS:
          hosts:
            border-leaf-01:
              ansible_host: 192.168.1.30
            border-leaf-02:
              ansible_host: 192.168.1.31
"""
    (inventory_dir / "hosts.yml").write_text(hosts_content.strip())

    # Create group_vars structure
    group_vars = inventory_dir / "group_vars"
    group_vars.mkdir()

    # Common fabric configuration
    fabric_dir = group_vars / "AVD_FABRIC"
    fabric_dir.mkdir()
    fabric_content = """---
fabric_name: EXTENDED_TEST_FABRIC
design:
  type: l3ls-evpn

mgmt_gateway: 192.168.1.1
mgmt_interface: Management1

local_users:
  - name: admin
    privilege: 15
    role: network-admin
    sha512_password: "$6$hash_placeholder"
"""
    (fabric_dir / "avd.yml").write_text(fabric_content.strip())

    # Spine configuration
    spine_dir = group_vars / "AVD_SPINES"
    spine_dir.mkdir()
    spine_content = """---
type: spine
platform: cEOS-lab
spanning_tree:
  mode: none
"""
    (spine_dir / "avd.yml").write_text(spine_content.strip())

    # Leaf configuration
    leaf_dir = group_vars / "AVD_LEAFS"
    leaf_dir.mkdir()
    leaf_content = """---
type: leaf
platform: cEOS-lab
spanning_tree:
  mode: mstp
"""
    (leaf_dir / "avd.yml").write_text(leaf_content.strip())

    # Border leaf configuration
    border_dir = group_vars / "AVD_BORDER_LEAFS"
    border_dir.mkdir()
    border_content = """---
type: leaf
platform: cEOS-lab
spanning_tree:
  mode: mstp
border_leaf: true
"""
    (border_dir / "avd.yml").write_text(border_content.strip())

    return inventory_dir


@pytest.fixture(scope="function")
def output_workspace(integration_workspace: Path) -> Path:
    """
    Create a clean output workspace for test artifacts.

    Returns:
        Path: Path to the output directory
    """
    output_dir = integration_workspace / "output"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture(scope="function")
def mock_avd_generator():
    """
    Mock the AVD generator with predictable responses.

    This fixture mocks the external py-avd dependencies to provide
    consistent, predictable responses for integration testing.
    """
    with patch('avd_cli.logics.generator.get_avd_facts') as mock_facts, \
         patch('avd_cli.logics.generator.get_device_config') as mock_config, \
         patch('avd_cli.logics.generator.get_device_doc') as mock_doc:

        # Default structured config
        default_facts = {
            'spine-01': {
                'hostname': 'spine-01',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.10/24',
                'platform': 'cEOS-lab',
                'type': 'spine'
            },
            'leaf-01': {
                'hostname': 'leaf-01',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.20/24',
                'platform': 'cEOS-lab',
                'type': 'leaf'
            }
        }

        mock_facts.return_value = default_facts

        # Configuration generator
        def generate_config(avd_facts: Dict[str, Any], hostname: str) -> str:
            device_facts = avd_facts.get(hostname, {})
            return f"""!
! Configuration for {hostname}
! Platform: {device_facts.get('platform', 'unknown')}
!
hostname {hostname}
!
interface Management1
   ip address {device_facts.get('mgmt_ip', '192.168.1.1/24')}
   no shutdown
!
{f"! Device type: {device_facts.get('type', 'unknown')}" if 'type' in device_facts else ""}
!
end
""".strip()

        mock_config.side_effect = generate_config

        # Documentation generator
        def generate_doc(avd_facts: Dict[str, Any], hostname: str) -> str:
            device_facts = avd_facts.get(hostname, {})
            return f"""# {hostname}

## Device Information

- **Hostname**: {hostname}
- **Platform**: {device_facts.get('platform', 'unknown')}
- **Type**: {device_facts.get('type', 'unknown')}
- **Management IP**: {device_facts.get('mgmt_ip', 'unknown')}

## Configuration Summary

This device is configured with basic management interface and platform-specific settings.

### Management Interface

The management interface is configured with IP address {device_facts.get('mgmt_ip', 'unknown')}.
""".strip()

        mock_doc.side_effect = generate_doc

        yield {
            'facts': mock_facts,
            'config': mock_config,
            'doc': mock_doc,
            'default_facts': default_facts
        }


@pytest.fixture(scope="function")
def mock_avd_generator_extended():
    """
    Extended mock for AVD generator with more devices.

    This fixture provides mocking for more complex test scenarios
    with multiple device types and configurations.
    """
    with patch('avd_cli.logics.generator.get_avd_facts') as mock_facts, \
         patch('avd_cli.logics.generator.get_device_config') as mock_config, \
         patch('avd_cli.logics.generator.get_device_doc') as mock_doc:

        # Extended structured config
        extended_facts = {
            'spine-01': {
                'hostname': 'spine-01',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.10/24',
                'platform': 'cEOS-lab',
                'type': 'spine'
            },
            'spine-02': {
                'hostname': 'spine-02',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.11/24',
                'platform': 'cEOS-lab',
                'type': 'spine'
            },
            'leaf-01': {
                'hostname': 'leaf-01',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.20/24',
                'platform': 'cEOS-lab',
                'type': 'leaf'
            },
            'leaf-02': {
                'hostname': 'leaf-02',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.21/24',
                'platform': 'cEOS-lab',
                'type': 'leaf'
            },
            'border-leaf-01': {
                'hostname': 'border-leaf-01',
                'is_deployed': True,
                'mgmt_ip': '192.168.1.30/24',
                'platform': 'cEOS-lab',
                'type': 'leaf',
                'border_leaf': True
            }
        }

        mock_facts.return_value = extended_facts

        # Use same generators as basic mock
        def generate_config(avd_facts: Dict[str, Any], hostname: str) -> str:
            device_facts = avd_facts.get(hostname, {})
            config_lines = [
                "!",
                f"! Configuration for {hostname}",
                f"! Platform: {device_facts.get('platform', 'unknown')}",
                "!",
                f"hostname {hostname}",
                "!"
            ]

            # Management interface
            config_lines.extend([
                "interface Management1",
                f"   ip address {device_facts.get('mgmt_ip', '192.168.1.1/24')}",
                "   no shutdown",
                "!"
            ])

            # Device-specific configuration
            if device_facts.get('type') == 'spine':
                config_lines.extend([
                    "! Spine-specific configuration",
                    "spanning-tree mode none",
                    "!"
                ])
            elif device_facts.get('type') == 'leaf':
                config_lines.extend([
                    "! Leaf-specific configuration",
                    "spanning-tree mode mstp",
                    "!"
                ])

                if device_facts.get('border_leaf'):
                    config_lines.extend([
                        "! Border leaf configuration",
                        "router bgp 65001",
                        "   neighbor 10.0.0.1 remote-as 65000",
                        "!"
                    ])

            config_lines.append("end")
            return "\n".join(config_lines)

        mock_config.side_effect = generate_config

        def generate_doc(avd_facts: Dict[str, Any], hostname: str) -> str:
            device_facts = avd_facts.get(hostname, {})
            doc_lines = [
                f"# {hostname}",
                "",
                "## Device Information",
                "",
                f"- **Hostname**: {hostname}",
                f"- **Platform**: {device_facts.get('platform', 'unknown')}",
                f"- **Type**: {device_facts.get('type', 'unknown')}",
                f"- **Management IP**: {device_facts.get('mgmt_ip', 'unknown')}"
            ]

            if device_facts.get('border_leaf'):
                doc_lines.append("- **Role**: Border Leaf")

            doc_lines.extend([
                "",
                "## Configuration Summary",
                "",
                "This device is configured with the following features:",
                ""
            ])

            if device_facts.get('type') == 'spine':
                doc_lines.append("- Spine functionality with no spanning-tree")
            elif device_facts.get('type') == 'leaf':
                doc_lines.append("- Leaf functionality with MSTP spanning-tree")
                if device_facts.get('border_leaf'):
                    doc_lines.append("- Border leaf with external BGP peering")

            return "\n".join(doc_lines)

        mock_doc.side_effect = generate_doc

        yield {
            'facts': mock_facts,
            'config': mock_config,
            'doc': mock_doc,
            'extended_facts': extended_facts
        }


@pytest.fixture(scope="function")
def inventory_loader():
    """
    Provide a real InventoryLoader instance for integration testing.

    This fixture creates an actual InventoryLoader instance rather than
    a mock, allowing integration tests to exercise the real loading logic.
    """
    return InventoryLoader()


@pytest.fixture(scope="function")
def avd_configuration_generator():
    """
    Provide a real ConfigurationGenerator instance for integration testing.

    This fixture creates an actual ConfigurationGenerator instance rather than
    a mock, but external dependencies (py-avd) should still be mocked
    in integration tests.
    """
    return ConfigurationGenerator()


# Pytest hooks for integration test customization
def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "filesystem: mark test as using filesystem"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for integration tests."""
    # Automatically mark all tests in integration directory
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

            # Mark filesystem tests
            if "filesystem" in item.name or "file" in item.name:
                item.add_marker(pytest.mark.filesystem)

            # Mark slow tests
            if "slow" in item.name or hasattr(item, "slow"):
                item.add_marker(pytest.mark.slow)


# Environment variable fixtures for integration testing
@pytest.fixture(scope="function")
def clean_environment():
    """
    Provide a clean environment for integration tests.

    This fixture temporarily clears certain environment variables
    that might affect test behavior, then restores them.
    """
    # Environment variables that might affect AVD CLI behavior
    env_vars_to_clear = [
        'AVD_CLI_CONFIG',
        'AVD_CLI_VERBOSE',
        'AVD_CLI_OUTPUT',
        'ANSIBLE_INVENTORY',
        'ANSIBLE_CONFIG'
    ]

    # Save original values
    original_values = {}
    for var in env_vars_to_clear:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


if __name__ == "__main__":
    # This file should not be run directly
    raise RuntimeError("This is a pytest configuration file, not a script")
