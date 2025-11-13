"""Unit tests for DeviceFilter class."""

from ipaddress import IPv4Address

import pytest

from avd_cli.models.inventory import DeviceDefinition
from avd_cli.utils.device_filter import DeviceFilter


class TestDeviceFilter:
    """Test cases for DeviceFilter class."""

    @pytest.fixture
    def sample_devices(self) -> list[DeviceDefinition]:
        """Create sample devices for testing.

        Returns
        -------
        list[DeviceDefinition]
            List of sample device definitions
        """
        return [
            DeviceDefinition(
                hostname="spine01",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.0.10"),
                device_type="spine",
                fabric="DC1_FABRIC",
                groups=["dc1", "spines", "dc1_spines"],
            ),
            DeviceDefinition(
                hostname="spine02",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.0.11"),
                device_type="spine",
                fabric="DC1_FABRIC",
                groups=["dc1", "spines", "dc1_spines"],
            ),
            DeviceDefinition(
                hostname="leaf01",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.0.20"),
                device_type="leaf",
                fabric="DC1_FABRIC",
                groups=["dc1", "leaves", "dc1_leaves", "pod1"],
            ),
            DeviceDefinition(
                hostname="leaf02",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.0.21"),
                device_type="leaf",
                fabric="DC1_FABRIC",
                groups=["dc1", "leaves", "dc1_leaves", "pod1"],
            ),
            DeviceDefinition(
                hostname="border01",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.0.30"),
                device_type="border_leaf",
                fabric="DC1_FABRIC",
                groups=["dc1", "border_leaves"],
            ),
            DeviceDefinition(
                hostname="spine03",
                platform="vEOS-lab",
                mgmt_ip=IPv4Address("192.168.1.10"),
                device_type="spine",
                fabric="DC2_FABRIC",
                groups=["dc2", "spines", "dc2_spines"],
            ),
        ]

    def test_no_filter_returns_all_devices(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that no filter returns all devices.

        Given: Device filter with no patterns
        When: Filtering devices
        Then: All devices are returned
        """
        device_filter = DeviceFilter()

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == len(sample_devices)
        assert result == sample_devices

    def test_filter_by_exact_hostname(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by exact hostname.

        Given: Device filter with exact hostname pattern
        When: Filtering devices
        Then: Only matching hostname is returned
        """
        device_filter = DeviceFilter(["spine01"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 1
        assert result[0].hostname == "spine01"

    def test_filter_by_hostname_wildcard(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by hostname with wildcard.

        Given: Device filter with hostname wildcard pattern
        When: Filtering devices
        Then: All matching hostnames are returned
        """
        device_filter = DeviceFilter(["spine*"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 3  # spine01, spine02, spine03
        assert all("spine" in d.hostname for d in result)

    def test_filter_by_hostname_range(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by hostname with range.

        Given: Device filter with hostname range pattern
        When: Filtering devices
        Then: Devices in range are returned
        """
        device_filter = DeviceFilter(["spine0[1:2]"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 2  # spine01, spine02
        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine01", "spine02"}

    def test_filter_by_group(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by group name.

        Given: Device filter with group pattern
        When: Filtering devices
        Then: All devices in that group are returned
        """
        device_filter = DeviceFilter(["spines"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 3  # All spine devices
        assert all("spine" in d.hostname for d in result)

    def test_filter_by_specific_group(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by specific group.

        Given: Device filter with specific group pattern
        When: Filtering devices
        Then: Only devices in that specific group are returned
        """
        device_filter = DeviceFilter(["dc1_spines"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 2  # Only DC1 spines
        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine01", "spine02"}

    def test_filter_by_fabric(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by fabric.

        Given: Device filter with fabric pattern
        When: Filtering devices
        Then: All devices in that fabric are returned
        """
        device_filter = DeviceFilter(["DC1_FABRIC"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 5  # All DC1 devices
        assert all(d.fabric == "DC1_FABRIC" for d in result)

    def test_filter_by_fabric_wildcard(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by fabric with wildcard.

        Given: Device filter with fabric wildcard pattern
        When: Filtering devices
        Then: All matching fabrics are returned
        """
        device_filter = DeviceFilter(["DC*_FABRIC"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 6  # All devices

    def test_filter_with_exclusion(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering with exclusion pattern.

        Given: Device filter with exclusion pattern on hostname only
        When: Filtering devices
        Then: Devices matching wildcard but not exclusion are returned

        Note: Since devices match by hostname OR groups OR fabric, spine01 is excluded
        by hostname, but other spines still match by hostname pattern.
        """
        device_filter = DeviceFilter(["spine0[1:2]", "!spine01"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 1  # spine02 only (spine01 excluded, spine03 not in range)
        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine02"}

    def test_filter_multiple_patterns(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering with multiple inclusion patterns.

        Given: Device filter with multiple patterns
        When: Filtering devices
        Then: Devices matching ANY pattern are returned
        """
        device_filter = DeviceFilter(["spine01", "leaf01", "border01"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 3
        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine01", "leaf01", "border01"}

    def test_filter_by_group_and_hostname(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by both group and hostname.

        Given: Device filter with group and hostname patterns
        When: Filtering devices
        Then: Devices matching either are returned
        """
        device_filter = DeviceFilter(["pod1", "spine01"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 3  # spine01, leaf01, leaf02
        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine01", "leaf01", "leaf02"}

    def test_filter_no_matches_raises_error(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that no matches raises ValueError.

        Given: Device filter with pattern that matches nothing
        When: Filtering devices
        Then: ValueError is raised with helpful message
        """
        device_filter = DeviceFilter(["nonexistent*"])

        with pytest.raises(ValueError, match="did not match any devices"):
            device_filter.filter_devices(sample_devices)

    def test_filter_error_includes_available_hostnames(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that error message includes available hostnames.

        Given: Device filter with pattern that matches nothing
        When: Filtering devices
        Then: Error includes list of available hostnames
        """
        device_filter = DeviceFilter(["nonexistent"])

        with pytest.raises(ValueError, match="Available hostnames"):
            device_filter.filter_devices(sample_devices)

    def test_filter_error_includes_available_groups(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that error message includes available groups.

        Given: Device filter with pattern that matches nothing
        When: Filtering devices
        Then: Error includes list of available groups
        """
        device_filter = DeviceFilter(["nonexistent"])

        with pytest.raises(ValueError, match="Available groups"):
            device_filter.filter_devices(sample_devices)

    def test_filter_error_includes_available_fabrics(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that error message includes available fabrics.

        Given: Device filter with pattern that matches nothing
        When: Filtering devices
        Then: Error includes list of available fabrics
        """
        device_filter = DeviceFilter(["nonexistent"])

        with pytest.raises(ValueError, match="Available fabrics"):
            device_filter.filter_devices(sample_devices)

    def test_get_matched_devices_summary(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test getting summary of matched devices by pattern.

        Given: Device filter with multiple patterns
        When: Getting matched devices summary
        Then: Returns dict mapping patterns to matched hostnames
        """
        device_filter = DeviceFilter(["spine*", "leaf01"])

        summary = device_filter.get_matched_devices_summary(sample_devices)

        assert "spine*" in summary
        assert "leaf01" in summary
        assert len(summary["spine*"]) == 3
        assert summary["leaf01"] == ["leaf01"]

    def test_filter_complex_combination(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test complex filter combination.

        Given: Device filter with ranges, wildcards, groups, and exclusions
        When: Filtering devices
        Then: Complex logic is applied correctly
        """
        device_filter = DeviceFilter([
            "spine0[1:2]",  # spine01, spine02
            "border*",       # border01
            "!spine02",      # Exclude spine02
        ])

        result = device_filter.filter_devices(sample_devices)

        hostnames = {d.hostname for d in result}
        assert hostnames == {"spine01", "border01"}  # spine02 excluded

    def test_filter_by_hierarchical_groups(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test filtering by hierarchical group structure.

        Given: Devices with multiple group levels
        When: Filtering by parent group
        Then: All devices in group hierarchy are returned
        """
        device_filter = DeviceFilter(["dc1"])

        result = device_filter.filter_devices(sample_devices)

        assert len(result) == 5  # All DC1 devices
        assert all("dc1" in d.groups for d in result)

    def test_repr(self) -> None:
        """Test string representation of DeviceFilter.

        Given: DeviceFilter instance
        When: Getting string representation
        Then: Returns formatted string with patterns
        """
        device_filter = DeviceFilter(["spine*", "leaf*"])

        repr_str = repr(device_filter)

        assert "DeviceFilter" in repr_str
        assert "spine*" in repr_str or "['spine*', 'leaf*']" in repr_str

    def test_filter_preserves_device_order(self, sample_devices: list[DeviceDefinition]) -> None:
        """Test that filtering preserves original device order.

        Given: Ordered list of devices
        When: Filtering devices
        Then: Filtered list maintains relative order
        """
        device_filter = DeviceFilter(["spine0[1:2]", "border*"])

        result = device_filter.filter_devices(sample_devices)

        # Check that spine devices come before border (as in original list)
        # spine01, spine02, border01
        assert len(result) == 3
        spine_indices = [i for i, d in enumerate(result) if "spine" in d.hostname]
        border_indices = [i for i, d in enumerate(result) if "border" in d.hostname]

        if spine_indices and border_indices:
            assert max(spine_indices) < min(border_indices)
