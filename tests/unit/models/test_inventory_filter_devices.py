#!/usr/bin/env python
# coding: utf-8
# pylint: disable=line-too-long
"""Unit tests for InventoryData.filter_devices method.

These tests cover the device filtering functionality to improve coverage
of lines 349-382 in inventory.py.
"""

from pathlib import Path

import pytest

from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData
from avd_cli.utils.device_filter import DeviceFilter


@pytest.fixture
def sample_inventory_with_devices(tmp_path: Path) -> InventoryData:
    """Create a sample inventory with various device types.

    Returns
    -------
    InventoryData
        Inventory with spine, leaf, and border leaf devices
    """
    # Create devices
    spine1 = DeviceDefinition(
        hostname="spine-01",
        platform="cEOS",
        mgmt_ip="192.168.1.1",
        device_type="spine",
        fabric="TEST_FABRIC",
    )
    spine2 = DeviceDefinition(
        hostname="spine-02",
        platform="cEOS",
        mgmt_ip="192.168.1.2",
        device_type="spine",
        fabric="TEST_FABRIC",
    )
    leaf1 = DeviceDefinition(
        hostname="leaf-01",
        platform="cEOS",
        mgmt_ip="192.168.1.10",
        device_type="leaf",
        fabric="TEST_FABRIC",
    )
    leaf2 = DeviceDefinition(
        hostname="leaf-02",
        platform="cEOS",
        mgmt_ip="192.168.1.11",
        device_type="leaf",
        fabric="TEST_FABRIC",
    )
    border1 = DeviceDefinition(
        hostname="border-01",
        platform="cEOS",
        mgmt_ip="192.168.1.20",
        device_type="border_leaf",
        fabric="TEST_FABRIC",
    )

    # Create fabric with all device types
    fabric = FabricDefinition(
        name="TEST_FABRIC",
        design_type="l3ls-evpn",
        devices_by_type={
            "spine": [spine1, spine2],
            "leaf": [leaf1, leaf2],
            "border_leaf": [border1],
        },
    )

    # Create inventory
    inventory = InventoryData(fabrics=[fabric], root_path=tmp_path)
    return inventory


def test_filter_devices_by_hostname_pattern(sample_inventory_with_devices: InventoryData) -> None:
    """Test filtering devices by hostname pattern.

    Coverage: Lines 349-382 (filter logic)
    """
    device_filter = DeviceFilter(patterns=["spine-*"])
    sample_inventory_with_devices.filter_devices(device_filter)

    # Only spine devices should remain
    all_devices = sample_inventory_with_devices.get_all_devices()
    assert len(all_devices) == 2
    assert all(d.hostname.startswith("spine-") for d in all_devices)


def test_filter_devices_by_leaf_pattern(sample_inventory_with_devices: InventoryData) -> None:
    """Test filtering devices to keep only leaf devices.

    Coverage: Lines 359-362 (filtered_leaves logic)
    """
    device_filter = DeviceFilter(patterns=["leaf-*"])
    sample_inventory_with_devices.filter_devices(device_filter)

    all_devices = sample_inventory_with_devices.get_all_devices()
    assert len(all_devices) == 2
    assert all(d.hostname.startswith("leaf-") for d in all_devices)


def test_filter_devices_by_border_pattern(sample_inventory_with_devices: InventoryData) -> None:
    """Test filtering devices to keep only border leaf devices.

    Coverage: Lines 363-366 (filtered_borders logic)
    """
    device_filter = DeviceFilter(patterns=["border-*"])
    sample_inventory_with_devices.filter_devices(device_filter)

    all_devices = sample_inventory_with_devices.get_all_devices()
    assert len(all_devices) == 1
    assert all_devices[0].hostname == "border-01"


def test_filter_devices_multiple_patterns(sample_inventory_with_devices: InventoryData) -> None:
    """Test filtering with multiple patterns.

    Coverage: Lines 349-382 (multiple pattern matching)
    """
    device_filter = DeviceFilter(patterns=["spine-*", "border-*"])
    sample_inventory_with_devices.filter_devices(device_filter)

    all_devices = sample_inventory_with_devices.get_all_devices()
    assert len(all_devices) == 3
    hostnames = {d.hostname for d in all_devices}
    assert hostnames == {"spine-01", "spine-02", "border-01"}


def test_filter_devices_no_matches_raises_error(sample_inventory_with_devices: InventoryData) -> None:
    """Test that filtering with no matches raises ValueError.

    Coverage: Lines 380-382 (error when no devices match)
    """
    device_filter = DeviceFilter(patterns=["nonexistent-*"])

    with pytest.raises(ValueError, match="No devices matched the filter patterns"):
        sample_inventory_with_devices.filter_devices(device_filter)


def test_filter_devices_with_none_filter(sample_inventory_with_devices: InventoryData) -> None:
    """Test that passing None filter returns immediately without filtering.

    Coverage: Lines 349-350 (early return when filter is None)
    """
    original_count = len(sample_inventory_with_devices.get_all_devices())
    sample_inventory_with_devices.filter_devices(None)

    # All devices should remain
    assert len(sample_inventory_with_devices.get_all_devices()) == original_count


def test_filter_devices_clears_and_extends_lists(sample_inventory_with_devices: InventoryData) -> None:
    """Test that filter_devices properly clears and updates device lists in-place.

    Coverage: Lines 368-375 (clear and extend logic)
    """
    fabric = sample_inventory_with_devices.fabrics[0]
    original_spine_count = len(fabric.spine_devices)

    # Filter to keep only spines
    device_filter = DeviceFilter(patterns=["spine-*"])
    sample_inventory_with_devices.filter_devices(device_filter)

    # Verify spine devices remain, others are cleared
    assert len(fabric.spine_devices) == original_spine_count
    assert len(fabric.leaf_devices) == 0
    assert len(fabric.border_leaf_devices) == 0
