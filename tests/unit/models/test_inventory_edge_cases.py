#!/usr/bin/env python
# coding: utf-8
# pylint: disable=line-too-long
"""Additional unit tests for inventory model edge cases.

This module adds test coverage for validation paths in DeviceDefinition
to reach 90% coverage target for avd_cli/models/inventory.py.
"""

import logging
from ipaddress import IPv4Address, IPv6Address

import pytest

from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


class TestDeviceDefinitionValidation:
    """Test DeviceDefinition validation logic."""

    def test_device_type_empty_raises_error(self) -> None:
        """Test that empty device_type raises ValueError.

        Coverage: lines 139-142
        """
        with pytest.raises(ValueError, match="Device type cannot be empty"):
            DeviceDefinition(
                hostname="test-device",
                platform="cEOS",
                mgmt_ip=IPv4Address("192.168.1.1"),
                device_type="",  # Empty device_type
                fabric="TEST_FABRIC",
            )

    def test_device_type_invalid_characters_raises_error(self) -> None:
        """Test that device_type with invalid characters raises ValueError.

        Coverage: lines 139-142
        """
        with pytest.raises(ValueError, match="Invalid device type format"):
            DeviceDefinition(
                hostname="test-device",
                platform="cEOS",
                mgmt_ip=IPv4Address("192.168.1.1"),
                device_type="spine-01",  # Contains hyphen
                fabric="TEST_FABRIC",
            )

    def test_device_type_with_special_characters_fails(self) -> None:
        """Test device_type with special characters fails validation."""
        with pytest.raises(ValueError, match="Invalid device type format"):
            DeviceDefinition(
                hostname="test-device",
                platform="cEOS",
                mgmt_ip=IPv4Address("192.168.1.1"),
                device_type="spine@device",  # Contains @
                fabric="TEST_FABRIC",
            )

    def test_device_type_custom_logs_debug_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that custom device_type logs debug warning but succeeds.

        Coverage: lines 149-158 (custom/MPLS type handling)
        """
        with caplog.at_level(logging.DEBUG):
            device = DeviceDefinition(
                hostname="test-device",
                platform="cEOS",
                mgmt_ip=IPv4Address("192.168.1.1"),
                device_type="custom_type",  # Valid alphanumeric + underscore
                fabric="TEST_FABRIC",
            )

        assert device.device_type == "custom_type"
        # Check that debug log was emitted
        assert any("custom_type" in record.message for record in caplog.records)
        assert any("not in standard types" in record.message for record in caplog.records)

    def test_device_type_mpls_pe_accepted(self) -> None:
        """Test that MPLS PE device type is accepted.

        Coverage: MPLS design type support
        """
        device = DeviceDefinition(
            hostname="pe-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="pe",  # MPLS PE type
            fabric="MPLS_FABRIC",
        )
        assert device.device_type == "pe"

    def test_device_type_mpls_p_accepted(self) -> None:
        """Test that MPLS P device type is accepted."""
        device = DeviceDefinition(
            hostname="p-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="p",  # MPLS P type
            fabric="MPLS_FABRIC",
        )
        assert device.device_type == "p"

    def test_ip_address_string_normalization(self) -> None:
        """Test that string IP addresses are converted to IP objects.

        Coverage: lines 160-169 (_normalize_ip_addresses)
        """
        device = DeviceDefinition(
            hostname="test-device",
            platform="cEOS",
            mgmt_ip="192.168.1.1",  # String IP
            mgmt_gateway="192.168.1.254",  # String gateway
            device_type="leaf",
            fabric="TEST_FABRIC",
        )

        # Should be converted to IPv4Address
        assert isinstance(device.mgmt_ip, IPv4Address)
        assert isinstance(device.mgmt_gateway, IPv4Address)
        assert str(device.mgmt_ip) == "192.168.1.1"
        assert str(device.mgmt_gateway) == "192.168.1.254"

    def test_ipv6_address_string_normalization(self) -> None:
        """Test that string IPv6 addresses are normalized."""
        device = DeviceDefinition(
            hostname="test-device",
            platform="cEOS",
            mgmt_ip="2001:db8::1",  # String IPv6
            mgmt_gateway="2001:db8::ffff",
            device_type="leaf",
            fabric="TEST_FABRIC",
        )

        assert isinstance(device.mgmt_ip, IPv6Address)
        assert isinstance(device.mgmt_gateway, IPv6Address)


class TestFabricDefinitionEdgeCases:
    """Test FabricDefinition edge cases."""

    def test_fabric_with_empty_devices(self) -> None:
        """Test fabric can be created with no devices.

        Coverage: edge case handling
        """
        fabric = FabricDefinition(
            name="EMPTY_FABRIC",
            design_type="l3ls-evpn",
            devices_by_type={},
        )

        assert fabric.name == "EMPTY_FABRIC"
        assert len(fabric.get_all_devices()) == 0
        assert len(fabric.spine_devices) == 0
        assert len(fabric.leaf_devices) == 0

    def test_fabric_custom_device_types(self) -> None:
        """Test fabric with custom device types.

        Coverage: flexible device dictionary (lines 195-200)
        """
        custom_device = DeviceDefinition(
            hostname="custom-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="custom_role",
            fabric="CUSTOM_FABRIC",
        )

        fabric = FabricDefinition(
            name="CUSTOM_FABRIC",
            design_type="custom",
            devices_by_type={"custom_role": [custom_device]},
        )

        all_devices = fabric.get_all_devices()
        assert len(all_devices) == 1
        assert all_devices[0].device_type == "custom_role"


class TestInventoryDataValidation:
    """Test InventoryData validation methods."""

    def test_inventory_with_duplicate_hostnames_across_fabrics(self) -> None:
        """Test validation detects duplicate hostnames across fabrics.

        Coverage: lines 349-382 (duplicate hostname check)
        """
        device1 = DeviceDefinition(
            hostname="duplicate-device",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="spine",
            fabric="FABRIC1",
        )

        device2 = DeviceDefinition(
            hostname="duplicate-device",  # Same hostname
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.2.1"),
            device_type="leaf",
            fabric="FABRIC2",
        )

        fabric1 = FabricDefinition(
            name="FABRIC1",
            design_type="l3ls-evpn",
            devices_by_type={"spine": [device1]},
        )

        fabric2 = FabricDefinition(
            name="FABRIC2",
            design_type="l3ls-evpn",
            devices_by_type={"leaf": [device2]},
        )

        from pathlib import Path
        inventory = InventoryData(root_path=Path("/tmp"), fabrics=[fabric1, fabric2])

        # Validation should detect duplicate
        errors = inventory.validate()
        assert len(errors) > 0
        assert any("Duplicate hostname" in err for err in errors)

    def test_inventory_with_duplicate_ips(self) -> None:
        """Test validation detects duplicate management IPs.

        Coverage: lines 349-382 (duplicate IP check)
        """
        device1 = DeviceDefinition(
            hostname="device1",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.100"),  # Same IP
            device_type="spine",
            fabric="TEST_FABRIC",
        )

        device2 = DeviceDefinition(
            hostname="device2",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.100"),  # Duplicate IP
            device_type="leaf",
            fabric="TEST_FABRIC",
        )

        fabric = FabricDefinition(
            name="TEST_FABRIC",
            design_type="l3ls-evpn",
            devices_by_type={"spine": [device1], "leaf": [device2]},
        )

        from pathlib import Path
        inventory = InventoryData(root_path=Path("/tmp"), fabrics=[fabric])

        errors = inventory.validate()
        assert len(errors) > 0
        assert any("Duplicate management IP" in err for err in errors)

    def test_inventory_validation_with_no_spines(self) -> None:
        """Test validation fails when fabric has no spine devices.

        Coverage: lines 426-428 (spine validation for L3LS-EVPN)
        """
        leaf_device = DeviceDefinition(
            hostname="leaf-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="leaf",
            fabric="NO_SPINES_FABRIC",
        )

        fabric = FabricDefinition(
            name="NO_SPINES_FABRIC",
            design_type="l3ls-evpn",  # L3LS-EVPN requires spines
            devices_by_type={"leaf": [leaf_device]},  # No spines
        )

        from pathlib import Path
        inventory = InventoryData(root_path=Path("/tmp"), fabrics=[fabric])

        errors = inventory.validate()
        assert len(errors) > 0
        assert any("has no spine devices" in err for err in errors)

    def test_inventory_validation_passes_with_spines(self) -> None:
        """Test validation succeeds when all requirements met."""
        spine_device = DeviceDefinition(
            hostname="spine-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.1"),
            device_type="spine",
            fabric="VALID_FABRIC",
        )

        leaf_device = DeviceDefinition(
            hostname="leaf-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="leaf",
            fabric="VALID_FABRIC",
        )

        fabric = FabricDefinition(
            name="VALID_FABRIC",
            design_type="l3ls-evpn",
            devices_by_type={"spine": [spine_device], "leaf": [leaf_device]},
        )

        from pathlib import Path
        inventory = InventoryData(root_path=Path("/tmp"), fabrics=[fabric])

        # Should not raise
        inventory.validate()

    def test_inventory_non_l3ls_design_no_spine_check(self) -> None:
        """Test non-L3LS designs don't require spine validation.

        Coverage: other design types bypass spine check
        """
        leaf_device = DeviceDefinition(
            hostname="leaf-01",
            platform="cEOS",
            mgmt_ip=IPv4Address("192.168.1.10"),
            device_type="leaf",
            fabric="L2LS_FABRIC",
        )

        fabric = FabricDefinition(
            name="L2LS_FABRIC",
            design_type="l2ls",  # L2LS doesn't require spines
            devices_by_type={"leaf": [leaf_device]},
        )

        from pathlib import Path
        inventory = InventoryData(root_path=Path("/tmp"), fabrics=[fabric])

        # Should not raise (L2LS doesn't require spines)
        inventory.validate()
