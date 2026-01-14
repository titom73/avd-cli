#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for DeviceFilter utility class."""

from unittest.mock import MagicMock

from avd_cli.utils.device_filter import DeviceFilter, filter_devices


class TestDeviceFilterCreation:
    """Test DeviceFilter instance creation."""

    def test_from_patterns_with_valid_patterns(self):
        """Test creating filter with valid patterns."""
        patterns = ["leaf-*", "spine-1"]
        device_filter = DeviceFilter.from_patterns(patterns)
        assert device_filter is not None
        assert device_filter.patterns == patterns

    def test_from_patterns_with_none(self):
        """Test creating filter with None returns None."""
        assert DeviceFilter.from_patterns(None) is None

    def test_from_patterns_with_empty_list(self):
        """Test creating filter with empty list returns None."""
        assert DeviceFilter.from_patterns([]) is None

    def test_from_patterns_strips_whitespace(self):
        """Test that whitespace is stripped from patterns."""
        patterns = [" leaf-* ", "  spine-1"]
        device_filter = DeviceFilter.from_patterns(patterns)
        assert device_filter is not None
        assert device_filter.patterns == ["leaf-*", "spine-1"]

    def test_from_patterns_removes_empty_strings(self):
        """Test that empty strings are removed."""
        patterns = ["leaf-*", "", "  ", "spine-1"]
        device_filter = DeviceFilter.from_patterns(patterns)
        assert device_filter is not None
        assert device_filter.patterns == ["leaf-*", "spine-1"]

    def test_from_patterns_all_empty(self):
        """Test that all empty/whitespace patterns returns None."""
        patterns = ["", "  ", "   "]
        device_filter = DeviceFilter.from_patterns(patterns)
        assert device_filter is None


class TestHostnameMatching:
    """Test hostname pattern matching."""

    def test_exact_match(self):
        """Test exact hostname match."""
        device_filter = DeviceFilter(patterns=["leaf-1a"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("leaf-1b") is False

    def test_wildcard_suffix(self):
        """Test wildcard at end of pattern."""
        device_filter = DeviceFilter(patterns=["leaf-*"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("leaf-1b") is True
        assert device_filter.matches_hostname("spine-1") is False

    def test_wildcard_prefix(self):
        """Test wildcard at start of pattern."""
        device_filter = DeviceFilter(patterns=["*-1a"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("spine-1a") is True
        assert device_filter.matches_hostname("leaf-1b") is False

    def test_wildcard_middle(self):
        """Test wildcard in middle of pattern."""
        device_filter = DeviceFilter(patterns=["leaf-*-1a"])
        assert device_filter.matches_hostname("leaf-dc1-1a") is True
        assert device_filter.matches_hostname("leaf-dc2-1a") is True
        assert device_filter.matches_hostname("leaf-1a") is False

    def test_question_mark(self):
        """Test single character wildcard."""
        device_filter = DeviceFilter(patterns=["leaf-?a"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("leaf-2a") is True
        assert device_filter.matches_hostname("leaf-10a") is False

    def test_character_class(self):
        """Test character class pattern."""
        device_filter = DeviceFilter(patterns=["leaf-[12]a"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("leaf-2a") is True
        assert device_filter.matches_hostname("leaf-3a") is False

    def test_character_class_range(self):
        """Test character class with range."""
        device_filter = DeviceFilter(patterns=["leaf-[1-3]a"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("leaf-2a") is True
        assert device_filter.matches_hostname("leaf-3a") is True
        assert device_filter.matches_hostname("leaf-4a") is False

    def test_multiple_patterns(self):
        """Test matching against multiple patterns."""
        device_filter = DeviceFilter(patterns=["leaf-*", "spine-1"])
        assert device_filter.matches_hostname("leaf-1a") is True
        assert device_filter.matches_hostname("spine-1") is True
        assert device_filter.matches_hostname("spine-2") is False

    def test_case_sensitive(self):
        """Test that matching is case-sensitive."""
        device_filter = DeviceFilter(patterns=["Leaf-*"])
        assert device_filter.matches_hostname("Leaf-1a") is True
        assert device_filter.matches_hostname("leaf-1a") is False


class TestGroupMatching:
    """Test group name pattern matching."""

    def test_exact_group_match(self):
        """Test exact group name match."""
        device_filter = DeviceFilter(patterns=["LEAFS"])
        assert device_filter.matches_group("LEAFS") is True
        assert device_filter.matches_group("SPINES") is False

    def test_group_wildcard(self):
        """Test wildcard group match."""
        device_filter = DeviceFilter(patterns=["DC1_*"])
        assert device_filter.matches_group("DC1_LEAFS") is True
        assert device_filter.matches_group("DC1_SPINES") is True
        assert device_filter.matches_group("DC2_LEAFS") is False

    def test_group_question_mark(self):
        """Test question mark in group match."""
        device_filter = DeviceFilter(patterns=["DC?_LEAFS"])
        assert device_filter.matches_group("DC1_LEAFS") is True
        assert device_filter.matches_group("DC2_LEAFS") is True
        assert device_filter.matches_group("DC10_LEAFS") is False

    def test_multiple_group_patterns(self):
        """Test multiple group patterns."""
        device_filter = DeviceFilter(patterns=["*_LEAFS", "SPINES"])
        assert device_filter.matches_group("DC1_LEAFS") is True
        assert device_filter.matches_group("DC2_LEAFS") is True
        assert device_filter.matches_group("SPINES") is True
        assert device_filter.matches_group("BORDERS") is False


class TestDeviceMatching:
    """Test device matching (hostname OR groups)."""

    def test_matches_by_hostname(self):
        """Test device matches by hostname."""
        device_filter = DeviceFilter(patterns=["leaf-1a"])
        assert device_filter.matches_device("leaf-1a", ["LEAFS"]) is True

    def test_matches_by_group(self):
        """Test device matches by group."""
        device_filter = DeviceFilter(patterns=["LEAFS"])
        assert device_filter.matches_device("leaf-1a", ["LEAFS", "DC1"]) is True

    def test_matches_by_fabric(self):
        """Test device matches by fabric (included in groups)."""
        device_filter = DeviceFilter(patterns=["FABRIC_A"])
        assert device_filter.matches_device("leaf-1a", ["LEAFS", "FABRIC_A"]) is True

    def test_no_match(self):
        """Test device does not match."""
        device_filter = DeviceFilter(patterns=["spine-*"])
        assert device_filter.matches_device("leaf-1a", ["LEAFS"]) is False

    def test_matches_hostname_or_group(self):
        """Test device matches by hostname OR group."""
        device_filter = DeviceFilter(patterns=["leaf-1a", "SPINES"])
        # Matches by hostname
        assert device_filter.matches_device("leaf-1a", ["LEAFS"]) is True
        # Matches by group
        assert device_filter.matches_device("spine-1", ["SPINES"]) is True
        # No match
        assert device_filter.matches_device("border-1", ["BORDERS"]) is False

    def test_matches_any_group(self):
        """Test device matches if ANY group matches."""
        device_filter = DeviceFilter(patterns=["DC1_*"])
        assert device_filter.matches_device("leaf-1a", ["DC1_LEAFS", "FABRIC"]) is True
        assert device_filter.matches_device("leaf-2a", ["DC2_LEAFS", "FABRIC"]) is False

    def test_empty_groups_list(self):
        """Test device with empty groups list."""
        device_filter = DeviceFilter(patterns=["leaf-*"])
        assert device_filter.matches_device("leaf-1a", []) is True
        assert device_filter.matches_device("spine-1", []) is False


class TestDeviceFilterRepr:
    """Test string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        device_filter = DeviceFilter(patterns=["leaf-*", "spine-1"])
        assert repr(device_filter) == "DeviceFilter(patterns=['leaf-*', 'spine-1'])"


class TestFilterDevicesFunction:
    """Test the standalone filter_devices() function."""

    def _create_mock_device(self, hostname: str, groups: list, fabric: str) -> MagicMock:
        """Create a mock DeviceDefinition."""
        device = MagicMock()
        device.hostname = hostname
        device.groups = groups
        device.fabric = fabric
        return device

    def _create_mock_inventory(self, devices: list) -> MagicMock:
        """Create a mock InventoryData with given devices."""
        inventory = MagicMock()
        inventory.get_all_devices.return_value = devices
        return inventory

    def test_filter_devices_returns_all_when_no_filter(self) -> None:
        """Test filter_devices returns all devices when filter is None."""
        devices = [
            self._create_mock_device("leaf-1a", ["LEAFS"], "FABRIC_A"),
            self._create_mock_device("spine-1", ["SPINES"], "FABRIC_A"),
        ]
        inventory = self._create_mock_inventory(devices)

        result = filter_devices(inventory, device_filter=None)

        assert len(result) == 2
        assert result == devices
        inventory.get_all_devices.assert_called_once()

    def test_filter_devices_applies_filter(self) -> None:
        """Test filter_devices applies DeviceFilter correctly."""
        devices = [
            self._create_mock_device("leaf-1a", ["LEAFS"], "FABRIC_A"),
            self._create_mock_device("leaf-1b", ["LEAFS"], "FABRIC_A"),
            self._create_mock_device("spine-1", ["SPINES"], "FABRIC_A"),
            self._create_mock_device("spine-2", ["SPINES"], "FABRIC_A"),
        ]
        inventory = self._create_mock_inventory(devices)
        device_filter = DeviceFilter(patterns=["leaf-*"])

        result = filter_devices(inventory, device_filter)

        assert len(result) == 2
        assert all(d.hostname.startswith("leaf-") for d in result)

    def test_filter_devices_with_empty_inventory(self) -> None:
        """Test filter_devices with empty inventory."""
        inventory = self._create_mock_inventory([])

        result = filter_devices(inventory, device_filter=None)

        assert result == []

    def test_filter_devices_with_empty_inventory_and_filter(self) -> None:
        """Test filter_devices with empty inventory and active filter."""
        inventory = self._create_mock_inventory([])
        device_filter = DeviceFilter(patterns=["leaf-*"])

        result = filter_devices(inventory, device_filter)

        assert result == []

    def test_filter_devices_matches_by_group(self) -> None:
        """Test filter_devices matches devices by group membership."""
        devices = [
            self._create_mock_device("leaf-1a", ["DC1_LEAFS"], "FABRIC_A"),
            self._create_mock_device("spine-1", ["DC1_SPINES"], "FABRIC_A"),
            self._create_mock_device("leaf-2a", ["DC2_LEAFS"], "FABRIC_B"),
        ]
        inventory = self._create_mock_inventory(devices)
        device_filter = DeviceFilter(patterns=["DC1_*"])

        result = filter_devices(inventory, device_filter)

        assert len(result) == 2
        hostnames = [d.hostname for d in result]
        assert "leaf-1a" in hostnames
        assert "spine-1" in hostnames

    def test_filter_devices_matches_by_fabric(self) -> None:
        """Test filter_devices matches devices by fabric name."""
        devices = [
            self._create_mock_device("leaf-1a", ["LEAFS"], "FABRIC_A"),
            self._create_mock_device("spine-1", ["SPINES"], "FABRIC_A"),
            self._create_mock_device("leaf-2a", ["LEAFS"], "FABRIC_B"),
        ]
        inventory = self._create_mock_inventory(devices)
        device_filter = DeviceFilter(patterns=["FABRIC_A"])

        result = filter_devices(inventory, device_filter)

        assert len(result) == 2
        hostnames = [d.hostname for d in result]
        assert "leaf-1a" in hostnames
        assert "spine-1" in hostnames

    def test_filter_devices_no_matches_returns_empty(self) -> None:
        """Test filter_devices returns empty list when no devices match."""
        devices = [
            self._create_mock_device("leaf-1a", ["LEAFS"], "FABRIC_A"),
            self._create_mock_device("spine-1", ["SPINES"], "FABRIC_A"),
        ]
        inventory = self._create_mock_inventory(devices)
        device_filter = DeviceFilter(patterns=["border-*"])

        result = filter_devices(inventory, device_filter)

        assert result == []
