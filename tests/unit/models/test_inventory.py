#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for inventory data models.

Tests for DeviceDefinition, FabricDefinition, and InventoryData models.
Validates field validation, data normalization, and utility methods.

Acceptance Criteria Coverage:
- AC-011: Device definition validation
- AC-012: Management IP validation
- AC-013: Hostname format validation
- AC-014: Platform validation
- AC-015: Device type validation
- AC-016: Invalid hostname handling
- AC-017: Invalid IP address handling
"""

from ipaddress import IPv4Address, IPv6Address
from pathlib import Path

import pytest

from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


class TestDeviceDefinition:
    """Test DeviceDefinition validation and normalization."""

    def test_create_valid_device(self) -> None:
        """Test creating device with valid fields.

        Given: Valid device parameters
        When: Creating DeviceDefinition
        Then: Device is created successfully

        AC-011: Device definition validation
        """
        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip=IPv4Address("10.0.0.1"),
            device_type="spine",
            fabric="DC1",
        )

        assert device.hostname == "spine01"
        assert device.platform == "7050X3"
        assert device.mgmt_ip == IPv4Address("10.0.0.1")
        assert device.device_type == "spine"
        assert device.fabric == "DC1"

    def test_normalize_ip_from_string(self) -> None:
        """Test IP address normalization from string.

        Given: IP address as string
        When: Creating DeviceDefinition
        Then: IP is converted to IPv4Address object

        AC-012: Management IP validation
        """
        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )

        assert isinstance(device.mgmt_ip, IPv4Address)
        assert str(device.mgmt_ip) == "192.168.1.10"

    def test_normalize_ipv6_from_string(self) -> None:
        """Test IPv6 address normalization.

        Given: IPv6 address as string
        When: Creating DeviceDefinition
        Then: IP is converted to IPv6Address object

        AC-012: Management IP validation
        """
        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="2001:db8::1",
            device_type="spine",
            fabric="DC1",
        )

        assert isinstance(device.mgmt_ip, IPv6Address)
        assert str(device.mgmt_ip) == "2001:db8::1"

    def test_normalize_mgmt_gateway_from_string(self) -> None:
        """Test management gateway normalization.

        Given: Gateway IP as string
        When: Creating DeviceDefinition with mgmt_gateway
        Then: Gateway is converted to IPv4Address object

        AC-012: Management IP validation
        """
        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
            mgmt_gateway="192.168.1.1",
        )

        assert isinstance(device.mgmt_gateway, IPv4Address)
        assert str(device.mgmt_gateway) == "192.168.1.1"

    def test_invalid_hostname_empty(self) -> None:
        """Test validation of empty hostname.

        Given: Empty hostname
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-013: Hostname format validation
        AC-016: Invalid hostname handling
        """
        with pytest.raises(ValueError, match="Hostname cannot be empty"):
            DeviceDefinition(
                hostname="",
                platform="7050X3",
                mgmt_ip="192.168.1.10",
                device_type="spine",
                fabric="DC1",
            )

    def test_invalid_hostname_special_chars(self) -> None:
        """Test validation of hostname with special characters.

        Given: Hostname with invalid characters
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-013: Hostname format validation
        AC-016: Invalid hostname handling
        """
        with pytest.raises(ValueError, match="Invalid hostname format"):
            DeviceDefinition(
                hostname="spine@01",
                platform="7050X3",
                mgmt_ip="192.168.1.10",
                device_type="spine",
                fabric="DC1",
            )

    def test_invalid_hostname_too_long(self) -> None:
        """Test validation of overly long hostname.

        Given: Hostname exceeding 63 characters
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-013: Hostname format validation
        AC-016: Invalid hostname handling
        """
        long_hostname = "a" * 64
        with pytest.raises(ValueError, match="Hostname too long"):
            DeviceDefinition(
                hostname=long_hostname,
                platform="7050X3",
                mgmt_ip="192.168.1.10",
                device_type="spine",
                fabric="DC1",
            )

    def test_valid_hostname_with_hyphen_underscore(self) -> None:
        """Test valid hostname with hyphens and underscores.

        Given: Hostname with valid special chars (-, _)
        When: Creating DeviceDefinition
        Then: Device is created successfully

        AC-013: Hostname format validation
        """
        device = DeviceDefinition(
            hostname="spine-01_dc1",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )

        assert device.hostname == "spine-01_dc1"

    def test_invalid_platform(self) -> None:
        """Test validation of unsupported platform.

        Given: Unsupported platform name
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-014: Platform validation
        """
        with pytest.raises(ValueError, match="Unsupported platform"):
            DeviceDefinition(
                hostname="spine01",
                platform="InvalidPlatform123",
                mgmt_ip="192.168.1.10",
                device_type="spine",
                fabric="DC1",
            )

    def test_invalid_device_type(self) -> None:
        """Test validation of unsupported device type.

        Given: Unsupported device type
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-015: Device type validation
        """
        with pytest.raises(ValueError, match="Invalid device type"):
            DeviceDefinition(
                hostname="spine01",
                platform="7050X3",
                mgmt_ip="192.168.1.10",
                device_type="invalid_type",
                fabric="DC1",
            )

    def test_invalid_ip_address(self) -> None:
        """Test validation of invalid IP address.

        Given: Invalid IP address string
        When: Creating DeviceDefinition
        Then: ValueError is raised

        AC-012: Management IP validation
        AC-017: Invalid IP address handling
        """
        with pytest.raises(ValueError):
            DeviceDefinition(
                hostname="spine01",
                platform="7050X3",
                mgmt_ip="999.999.999.999",
                device_type="spine",
                fabric="DC1",
            )

    def test_device_with_optional_fields(self) -> None:
        """Test device creation with optional fields.

        Given: Device with pod, rack, and other optional fields
        When: Creating DeviceDefinition
        Then: All fields are set correctly

        AC-011: Device definition validation
        """
        device = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
            pod="POD1",
            rack="RACK1",
            serial_number="ABC123",
            system_mac_address="00:1c:73:00:00:01",
            structured_config={"vlan": 10},
            custom_variables={"role": "access"},
        )

        assert device.pod == "POD1"
        assert device.rack == "RACK1"
        assert device.serial_number == "ABC123"
        assert device.system_mac_address == "00:1c:73:00:00:01"
        assert device.structured_config == {"vlan": 10}
        assert device.custom_variables == {"role": "access"}

    def test_device_default_optional_fields(self) -> None:
        """Test default values for optional fields.

        Given: Device created without optional fields
        When: Creating DeviceDefinition
        Then: Optional fields have correct defaults

        AC-011: Device definition validation
        """
        device = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )

        assert device.pod is None
        assert device.rack is None
        assert device.mgmt_gateway is None
        assert device.serial_number is None
        assert device.system_mac_address is None
        assert device.structured_config == {}
        assert device.custom_variables == {}


class TestFabricDefinition:
    """Test FabricDefinition model and methods."""

    def test_create_fabric(self) -> None:
        """Test fabric creation with devices.

        Given: Fabric with spine and leaf devices
        When: Creating FabricDefinition
        Then: Fabric is created with all devices
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf],
        )

        assert fabric.name == "DC1"
        assert fabric.design_type == "l3ls-evpn"
        assert len(fabric.spine_devices) == 1
        assert len(fabric.leaf_devices) == 1

    def test_get_all_devices(self) -> None:
        """Test retrieving all devices from fabric.

        Given: Fabric with multiple device types
        When: Calling get_all_devices()
        Then: Returns combined list of all devices
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )
        border = DeviceDefinition(
            hostname="border01",
            platform="7280R3",
            mgmt_ip="192.168.1.30",
            device_type="border_leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf],
            border_leaf_devices=[border],
        )

        all_devices = fabric.get_all_devices()
        assert len(all_devices) == 3
        assert spine in all_devices
        assert leaf in all_devices
        assert border in all_devices

    def test_get_devices_by_type_spine(self) -> None:
        """Test filtering devices by type - spine.

        Given: Fabric with multiple device types
        When: Calling get_devices_by_type('spine')
        Then: Returns only spine devices
        """
        spine1 = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        spine2 = DeviceDefinition(
            hostname="spine02",
            platform="7050X3",
            mgmt_ip="192.168.1.11",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine1, spine2],
            leaf_devices=[leaf],
        )

        spines = fabric.get_devices_by_type("spine")
        assert len(spines) == 2
        assert spine1 in spines
        assert spine2 in spines
        assert leaf not in spines

    def test_get_devices_by_type_leaf(self) -> None:
        """Test filtering devices by type - leaf.

        Given: Fabric with multiple device types
        When: Calling get_devices_by_type('leaf')
        Then: Returns only leaf devices
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf1 = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )
        leaf2 = DeviceDefinition(
            hostname="leaf02",
            platform="722XP",
            mgmt_ip="192.168.1.21",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf1, leaf2],
        )

        leaves = fabric.get_devices_by_type("leaf")
        assert len(leaves) == 2
        assert leaf1 in leaves
        assert leaf2 in leaves
        assert spine not in leaves

    def test_fabric_default_settings(self) -> None:
        """Test default fabric-wide settings.

        Given: Fabric created without custom settings
        When: Creating FabricDefinition
        Then: Default VLAN IDs are set correctly
        """
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
        )

        assert fabric.mlag_peer_l3_vlan == 4093
        assert fabric.mlag_peer_vlan == 4094
        assert fabric.bgp_asn_range is None

    def test_fabric_custom_settings(self) -> None:
        """Test fabric with custom settings.

        Given: Fabric with custom VLAN IDs and ASN range
        When: Creating FabricDefinition
        Then: Custom settings are applied
        """
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            bgp_asn_range="65000-65100",
            mlag_peer_l3_vlan=3999,
            mlag_peer_vlan=4000,
        )

        assert fabric.bgp_asn_range == "65000-65100"
        assert fabric.mlag_peer_l3_vlan == 3999
        assert fabric.mlag_peer_vlan == 4000


class TestInventoryData:
    """Test InventoryData model and methods."""

    def test_create_inventory(self, tmp_path: Path) -> None:
        """Test inventory creation.

        Given: Path and fabric list
        When: Creating InventoryData
        Then: Inventory is created with all fabrics
        """
        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
        )

        inventory = InventoryData(
            root_path=tmp_path,
            fabrics=[fabric],
            global_vars={"dns_servers": ["8.8.8.8"]},
        )

        assert inventory.root_path == tmp_path
        assert len(inventory.fabrics) == 1
        assert inventory.global_vars == {"dns_servers": ["8.8.8.8"]}

    def test_get_all_devices_across_fabrics(self) -> None:
        """Test retrieving devices across multiple fabrics.

        Given: Inventory with multiple fabrics
        When: Calling get_all_devices()
        Then: Returns devices from all fabrics
        """
        spine1 = DeviceDefinition(
            hostname="dc1-spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        spine2 = DeviceDefinition(
            hostname="dc2-spine01",
            platform="7050X3",
            mgmt_ip="192.168.2.10",
            device_type="spine",
            fabric="DC2",
        )

        fabric1 = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine1],
        )
        fabric2 = FabricDefinition(
            name="DC2",
            design_type="l3ls-evpn",
            spine_devices=[spine2],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric1, fabric2],
        )

        all_devices = inventory.get_all_devices()
        assert len(all_devices) == 2
        assert spine1 in all_devices
        assert spine2 in all_devices

    def test_get_device_by_hostname_found(self) -> None:
        """Test finding device by hostname.

        Given: Inventory with devices
        When: Calling get_device_by_hostname() with valid hostname
        Then: Returns matching device
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        device = inventory.get_device_by_hostname("leaf01")
        assert device is not None
        assert device.hostname == "leaf01"
        assert device.platform == "722XP"

    def test_get_device_by_hostname_not_found(self) -> None:
        """Test searching for non-existent hostname.

        Given: Inventory with devices
        When: Calling get_device_by_hostname() with invalid hostname
        Then: Returns None
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        device = inventory.get_device_by_hostname("nonexistent")
        assert device is None

    def test_validate_duplicate_hostnames(self) -> None:
        """Test validation catches duplicate hostnames.

        Given: Inventory with duplicate hostnames
        When: Calling validate()
        Then: Returns error about duplicate hostnames
        """
        device1 = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        device2 = DeviceDefinition(
            hostname="spine01",  # Duplicate
            platform="7050X3",
            mgmt_ip="192.168.1.11",
            device_type="spine",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[device1, device2],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        errors = inventory.validate()
        assert len(errors) > 0
        assert any("Duplicate hostnames" in err for err in errors)

    def test_validate_duplicate_ips(self) -> None:
        """Test validation catches duplicate IPs.

        Given: Inventory with duplicate management IPs
        When: Calling validate()
        Then: Returns error about duplicate IPs
        """
        device1 = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        device2 = DeviceDefinition(
            hostname="spine02",
            platform="7050X3",
            mgmt_ip="192.168.1.10",  # Duplicate IP
            device_type="spine",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[device1, device2],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        errors = inventory.validate()
        assert len(errors) > 0
        assert any("Duplicate management IPs" in err for err in errors)

    def test_validate_fabric_no_spines(self) -> None:
        """Test validation warns about fabrics without spines.

        Given: Fabric with only leaf devices
        When: Calling validate()
        Then: Returns warning about missing spine devices
        """
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            leaf_devices=[leaf],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        errors = inventory.validate()
        assert len(errors) > 0
        assert any("no spine devices" in err for err in errors)

    def test_validate_valid_inventory(self) -> None:
        """Test validation passes for valid inventory.

        Given: Valid inventory with no issues
        When: Calling validate()
        Then: Returns empty error list
        """
        spine = DeviceDefinition(
            hostname="spine01",
            platform="7050X3",
            mgmt_ip="192.168.1.10",
            device_type="spine",
            fabric="DC1",
        )
        leaf = DeviceDefinition(
            hostname="leaf01",
            platform="722XP",
            mgmt_ip="192.168.1.20",
            device_type="leaf",
            fabric="DC1",
        )

        fabric = FabricDefinition(
            name="DC1",
            design_type="l3ls-evpn",
            spine_devices=[spine],
            leaf_devices=[leaf],
        )

        inventory = InventoryData(
            root_path=Path("/tmp"),
            fabrics=[fabric],
        )

        errors = inventory.validate()
        assert len(errors) == 0
