#!/usr/bin/env python
# coding: utf-8 -*-
# pylint: disable=line-too-long

"""
Unit tests for topology generation logic.

Tests focus on private helper methods that handle complex logic:
- _compute_mgmt_subnet: IP subnet calculation
- _build_nodes: Node configuration generation
- _build_links: Link topology construction
- _normalize_startup_dir: Path normalization
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from avd_cli.logics.topology import ContainerlabTopologyGenerator
from avd_cli.models.inventory import DeviceDefinition, InventoryData


class TestNormalizeStartupDir:
    """Test cases for _normalize_startup_dir() method."""

    @pytest.fixture
    def generator(self) -> ContainerlabTopologyGenerator:
        """Provide topology generator instance."""
        return ContainerlabTopologyGenerator()

    def test_normalize_startup_dir_none_uses_default(self, generator: ContainerlabTopologyGenerator) -> None:
        """Test that None startup_dir defaults to root_path/configs."""
        root_path = Path("/tmp/output")
        result = generator._normalize_startup_dir(root_path, None)

        assert result == root_path / "configs"

    def test_normalize_startup_dir_relative_path(self, generator: ContainerlabTopologyGenerator) -> None:
        """Test that relative paths are resolved relative to root_path."""
        root_path = Path("/tmp/output")
        startup_dir = Path("custom_configs")
        result = generator._normalize_startup_dir(root_path, startup_dir)

        assert result == root_path / "custom_configs"

    def test_normalize_startup_dir_absolute_path(self, generator: ContainerlabTopologyGenerator) -> None:
        """Test that absolute paths are used as-is."""
        root_path = Path("/tmp/output")
        startup_dir = Path("/etc/configs")
        result = generator._normalize_startup_dir(root_path, startup_dir)

        assert result == Path("/etc/configs")

    def test_normalize_startup_dir_string_input(self, generator: ContainerlabTopologyGenerator) -> None:
        """Test that string inputs are converted to Path."""
        root_path = Path("/tmp/output")
        startup_dir = "string_configs"
        result = generator._normalize_startup_dir(root_path, startup_dir)

        assert result == root_path / "string_configs"


class TestComputeMgmtSubnet:
    """Test cases for _compute_mgmt_subnet() method."""

    @pytest.fixture
    def generator(self) -> ContainerlabTopologyGenerator:
        """Provide topology generator instance."""
        return ContainerlabTopologyGenerator()

    @pytest.fixture
    def mock_inventory(self) -> InventoryData:
        """Provide mock inventory data."""
        inventory = MagicMock(spec=InventoryData)
        inventory.host_vars = {}
        return inventory

    def test_compute_mgmt_subnet_no_devices(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test subnet computation with no devices returns default."""
        devices = []
        result = generator._compute_mgmt_subnet(mock_inventory, devices)

        assert result == "172.20.20.0/24"

    def test_compute_mgmt_subnet_no_valid_ips(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test subnet computation with devices but no valid IPs returns default."""
        device = DeviceDefinition(
            hostname="device1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip=None
        )
        mock_inventory.host_vars = {"device1": {}}

        result = generator._compute_mgmt_subnet(mock_inventory, [device])

        assert result == "172.20.20.0/24"

    def test_compute_mgmt_subnet_single_ip(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test subnet computation with single IP."""
        device = DeviceDefinition(
            hostname="device1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip="192.168.0.10"
        )
        mock_inventory.host_vars = {"device1": {"ansible_host": "192.168.0.10"}}

        result = generator._compute_mgmt_subnet(mock_inventory, [device])

        # Single IP should use /30 (smallest useful subnet)
        assert result.startswith("192.168.0.")
        # Verify it's a valid CIDR notation
        assert "/" in result

    def test_compute_mgmt_subnet_multiple_ips_same_network(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test subnet computation with multiple IPs in same /24."""
        devices = [
            DeviceDefinition(
                hostname=f"device{i}",
                device_type="spine", platform="cEOSLab", fabric="TEST",
                
                
                mgmt_ip=f"192.168.0.{10+i}"
            )
            for i in range(4)
        ]
        mock_inventory.host_vars = {
            f"device{i}": {"ansible_host": f"192.168.0.{10+i}"}
            for i in range(4)
        }

        result = generator._compute_mgmt_subnet(mock_inventory, devices)

        # Should compute a subnet that contains all IPs
        assert result.startswith("192.168.0.")
        # Verify it's a valid CIDR notation
        assert "/" in result

    def test_compute_mgmt_subnet_skips_ipv6(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that IPv6 addresses are skipped."""
        devices = [
            DeviceDefinition(
                hostname="device1",
                device_type="spine", platform="cEOSLab", fabric="TEST",
                
                
                mgmt_ip="192.168.0.10"
            ),
            DeviceDefinition(
                hostname="device2",
                device_type="spine", platform="cEOSLab", fabric="TEST",
                
                
                mgmt_ip="2001:db8::1"
            ),
        ]
        mock_inventory.host_vars = {
            "device1": {"ansible_host": "192.168.0.10"},
            "device2": {"ansible_host": "2001:db8::1"},
        }

        result = generator._compute_mgmt_subnet(mock_inventory, devices)

        # Should only use IPv4 address
        assert result.startswith("192.168.0.")

    def test_compute_mgmt_subnet_handles_cidr_notation(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that IPs with /xx notation are handled correctly."""
        device = DeviceDefinition(
            hostname="device1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip="192.168.0.10"  # DeviceDefinition doesn't accept /24 notation
        )
        # But ansible_host can have /24 notation
        mock_inventory.host_vars = {"device1": {"ansible_host": "192.168.0.10/24"}}

        result = generator._compute_mgmt_subnet(mock_inventory, [device])

        # Should extract IP without /24 and compute subnet
        assert result.startswith("192.168.0.")
        assert "/" in result

    def test_compute_mgmt_subnet_bug_fix_regression(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that the bug fix for incorrect subnet calculation works.

        Regression test for RISK-008: IPs 192.168.0.10-15 should not compute
        as 192.168.0.8/29 where .8=network and .15=broadcast.
        """
        # Create devices with IPs .10 through .15
        devices = [
            DeviceDefinition(
                hostname=f"device{i}",
                device_type="spine", platform="cEOSLab", fabric="TEST",
                
                
                mgmt_ip=f"192.168.0.{i}"
            )
            for i in range(10, 16)  # 10, 11, 12, 13, 14, 15
        ]
        mock_inventory.host_vars = {
            f"device{i}": {"ansible_host": f"192.168.0.{i}"}
            for i in range(10, 16)
        }

        result = generator._compute_mgmt_subnet(mock_inventory, devices)

        # Should NOT be /29 (which would be .8/29 with .8 as network and .15 as broadcast)
        # Should be a larger subnet that includes all IPs as valid hosts
        import ipaddress
        network = ipaddress.ip_network(result)

        # Verify all IPs are valid host addresses (not network or broadcast)
        for i in range(10, 16):
            ip = ipaddress.ip_address(f"192.168.0.{i}")
            assert ip in network, f"IP {ip} should be in network {network}"
            assert ip != network.network_address, f"IP {ip} should not be network address"
            assert ip != network.broadcast_address, f"IP {ip} should not be broadcast address"


class TestBuildNodes:
    """Test cases for _build_nodes() method."""

    @pytest.fixture
    def generator(self) -> ContainerlabTopologyGenerator:
        """Provide topology generator instance."""
        return ContainerlabTopologyGenerator()

    @pytest.fixture
    def mock_inventory(self) -> InventoryData:
        """Provide mock inventory data."""
        inventory = MagicMock(spec=InventoryData)
        inventory.host_vars = {}
        inventory.group_vars = {}
        return inventory

    def test_build_nodes_empty_devices(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test building nodes with empty device list."""
        devices = []
        startup_dir = tmp_path / "configs"
        topology_path = tmp_path / "topology.clab.yml"

        with patch.object(generator, '_compute_topology_hierarchy', return_value={}):
            result = generator._build_nodes(
                mock_inventory, devices, startup_dir, "ceos", "arista/ceos:latest", topology_path
            )

        assert result == {}

    def test_build_nodes_skip_device_without_mgmt_ip(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test that devices without mgmt IP are skipped."""
        device = DeviceDefinition(
            hostname="device1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip=None
        )
        mock_inventory.host_vars = {"device1": {}}

        startup_dir = tmp_path / "configs"
        topology_path = tmp_path / "topology.clab.yml"

        with patch.object(generator, '_compute_topology_hierarchy', return_value={}):
            result = generator._build_nodes(
                mock_inventory, [device], startup_dir, "ceos", "arista/ceos:latest", topology_path
            )

        # Device should be skipped due to missing mgmt IP
        assert "device1" not in result

    def test_build_nodes_creates_node_config(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData, tmp_path: Path
    ) -> None:
        """Test that node configuration is created correctly."""
        device = DeviceDefinition(
            hostname="spine1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip="192.168.0.10"
        )
        mock_inventory.host_vars = {"spine1": {"ansible_host": "192.168.0.10"}}

        startup_dir = tmp_path / "configs"
        topology_path = tmp_path / "topology.clab.yml"

        with patch.object(generator, '_compute_topology_hierarchy', return_value={"spine1": 0}):
            result = generator._build_nodes(
                mock_inventory, [device], startup_dir, "ceos", "arista/ceos:4.29.3M", topology_path
            )

        assert "spine1" in result
        node_config = result["spine1"]

        # Verify node configuration structure
        assert node_config["kind"] == "ceos"
        assert node_config["image"] == "arista/ceos:4.29.3M"
        assert node_config["mgmt-ipv4"] == "192.168.0.10"
        assert "startup-config" in node_config
        assert "labels" in node_config
        # graph-level is an integer: max_depth - depth + 1 = 0 - 0 + 1 = 1
        assert node_config["labels"]["graph-level"] == 1
        assert node_config["labels"]["graph-icon"] == "router"


class TestBuildLinks:
    """Test cases for _build_links() method."""

    @pytest.fixture
    def generator(self) -> ContainerlabTopologyGenerator:
        """Provide topology generator instance."""
        return ContainerlabTopologyGenerator()

    @pytest.fixture
    def mock_inventory(self) -> InventoryData:
        """Provide mock inventory data."""
        inventory = MagicMock(spec=InventoryData)
        inventory.host_vars = {}
        inventory.group_vars = {}
        return inventory

    def test_build_links_empty_devices(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test building links with empty device list."""
        devices = []
        result = generator._build_links(mock_inventory, devices)

        assert result == []

    def test_build_links_no_ethernet_interfaces(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test building links when devices have no ethernet_interfaces."""
        device = DeviceDefinition(
            hostname="spine1",
            device_type="spine", platform="cEOSLab", fabric="TEST",
            
            
            mgmt_ip="192.168.0.10"
        )
        mock_inventory.host_vars = {"spine1": {}}

        result = generator._build_links(mock_inventory, [device])

        assert result == []

    def test_build_links_creates_link_from_ethernet_interfaces(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that links are created from ethernet_interfaces with peer info."""
        spine1 = DeviceDefinition(hostname="spine1", device_type="spine", platform="cEOSLab", fabric="TEST",   mgmt_ip="192.168.0.10")
        leaf1 = DeviceDefinition(hostname="leaf1", device_type="leaf", platform="cEOSLab", fabric="TEST",   mgmt_ip="192.168.0.20")

        mock_inventory.host_vars = {
            "spine1": {
                "ethernet_interfaces": [
                    {
                        "name": "Ethernet1",
                        "peer": "leaf1",
                        "peer_interface": "Ethernet1",
                        "description": "spine1_Ethernet1"
                    }
                ]
            },
            "leaf1": {}
        }

        result = generator._build_links(mock_inventory, [spine1, leaf1])

        # Should create one link
        assert len(result) == 1
        link = result[0]

        # Check endpoints (order may vary due to sorting)
        endpoints = link["endpoints"]
        assert "spine1:Ethernet1" in endpoints
        assert "leaf1:Ethernet1" in endpoints

    def test_build_links_deduplicates_bidirectional_links(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that bidirectional links are deduplicated."""
        spine1 = DeviceDefinition(hostname="spine1", device_type="spine", platform="cEOSLab", fabric="TEST",   mgmt_ip="192.168.0.10")
        leaf1 = DeviceDefinition(hostname="leaf1", device_type="leaf", platform="cEOSLab", fabric="TEST",   mgmt_ip="192.168.0.20")

        # Both devices have the same link defined
        mock_inventory.host_vars = {
            "spine1": {
                "ethernet_interfaces": [
                    {"name": "Ethernet1", "peer": "leaf1", "peer_interface": "Ethernet1"}
                ]
            },
            "leaf1": {
                "ethernet_interfaces": [
                    {"name": "Ethernet1", "peer": "spine1", "peer_interface": "Ethernet1"}
                ]
            }
        }

        result = generator._build_links(mock_inventory, [spine1, leaf1])

        # Should only create one link (deduplicated)
        assert len(result) == 1

    def test_build_links_skips_peer_not_in_device_list(
        self, generator: ContainerlabTopologyGenerator, mock_inventory: InventoryData
    ) -> None:
        """Test that links to peers not in device list are skipped."""
        spine1 = DeviceDefinition(hostname="spine1", device_type="spine", platform="cEOSLab", fabric="TEST",   mgmt_ip="192.168.0.10")

        mock_inventory.host_vars = {
            "spine1": {
                "ethernet_interfaces": [
                    {"name": "Ethernet1", "peer": "external-device", "peer_interface": "Ethernet1"}
                ]
            }
        }

        result = generator._build_links(mock_inventory, [spine1])

        # Should not create link to external device
        assert len(result) == 0
