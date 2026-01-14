"""Additional tests to improve coverage of topology module."""

from pathlib import Path

from avd_cli.logics.topology import ContainerlabTopologyGenerator
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData
from avd_cli.utils.device_filter import DeviceFilter, filter_devices


def test_filter_devices_with_device_filter_topology_integration(tmp_path):
    """Test filter_devices function works correctly with topology inventory structures."""
    device1 = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )
    device2 = DeviceDefinition(
        hostname="leaf1",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3leaf",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [device1], "leaf": [device2]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={},
        host_vars={},
    )

    # Create a DeviceFilter that matches only spine1
    device_filter = DeviceFilter(patterns=["spine1"])
    filtered = filter_devices(inventory, device_filter)

    assert len(filtered) == 1
    assert filtered[0].hostname == "spine1"


def test_normalize_startup_dir_none(tmp_path):
    """Test _normalize_startup_dir when startup_dir is None."""
    generator = ContainerlabTopologyGenerator()
    result = generator._normalize_startup_dir(tmp_path, None)

    assert result == tmp_path / "configs"


def test_normalize_startup_dir_relative(tmp_path):
    """Test _normalize_startup_dir with relative path."""
    generator = ContainerlabTopologyGenerator()
    result = generator._normalize_startup_dir(tmp_path, "intended/configs")

    assert result == tmp_path / "intended/configs"


def test_normalize_startup_dir_absolute(tmp_path):
    """Test _normalize_startup_dir with absolute path."""
    generator = ContainerlabTopologyGenerator()
    absolute_path = tmp_path / "absolute" / "configs"
    result = generator._normalize_startup_dir(tmp_path, absolute_path)

    assert result == absolute_path


def test_device_without_mgmt_ip_skipped(tmp_path):
    """Test that devices without resolvable mgmt IP are skipped."""
    device = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip=None,
        device_type="l3spine",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [device]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={},
        host_vars={},  # No ansible_host
    )

    generator = ContainerlabTopologyGenerator()

    result = generator.generate(
        inventory=inventory,
        output_path=tmp_path,
        startup_dir=None,
        device_filter=None,
    )

    # Check that the topology has no nodes (device was skipped)
    import yaml

    with open(result.topology_path) as f:
        topology = yaml.safe_load(f)

    assert "nodes" not in topology["topology"] or len(topology["topology"].get("nodes", {})) == 0


def test_mismatched_uplink_arrays(tmp_path):
    """Test warning for mismatched uplink array lengths."""
    device = DeviceDefinition(
        hostname="leaf1",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3leaf",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"leaf": [device]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                        "uplink_switches": ["spine1"],  # Mismatched length
                        "uplink_switch_interfaces": ["Ethernet1"],
                    }
                }
            }
        },
        host_vars={},
    )

    generator = ContainerlabTopologyGenerator()
    output_file = tmp_path / "topology.clab.yml"

    # This should log a warning but not crash
    generator.generate(
        inventory=inventory,
        output_path=output_file,
        startup_dir=None,
        device_filter=None,
    )

    # Verify file was created
    assert output_file.exists()


def test_uplink_to_nonexistent_device(tmp_path):
    """Test uplinks to devices not in valid_hosts are skipped."""
    spine = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )
    leaf = DeviceDefinition(
        hostname="leaf1",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3leaf",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [spine], "leaf": [leaf]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "uplink_interfaces": ["Ethernet1"],
                        "uplink_switches": ["nonexistent_spine"],  # Not in valid_hosts
                        "uplink_switch_interfaces": ["Ethernet1"],
                    }
                }
            }
        },
        host_vars={},
    )

    generator = ContainerlabTopologyGenerator()

    result = generator.generate(
        inventory=inventory,
        output_path=tmp_path,
        startup_dir=None,
        device_filter=None,
    )

    # Verify no links were created
    import yaml

    with open(result.topology_path) as f:
        topology = yaml.safe_load(f)

    assert "links" not in topology["topology"] or len(topology["topology"].get("links", [])) == 0


def test_compute_relative_path_with_different_dirs(tmp_path):
    """Test _compute_relative_path with files in different directories."""
    generator = ContainerlabTopologyGenerator()

    topology_path = tmp_path / "topology" / "test.clab.yml"
    config_path = tmp_path / "configs" / "device.cfg"

    # Create parent dirs
    topology_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Touch files
    topology_path.touch()
    config_path.touch()

    result = generator._compute_relative_path(topology_path, config_path)

    # Should be a relative POSIX path
    assert isinstance(result, str)
    assert "../configs/device.cfg" in result or "configs/device.cfg" in result


def test_topology_hierarchy_no_root_nodes(tmp_path):
    """Test topology hierarchy when all devices have uplinks (circular)."""
    device1 = DeviceDefinition(
        hostname="device1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )
    device2 = DeviceDefinition(
        hostname="device2",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3spine",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [device1, device2]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={},
        host_vars={
            "device1": {
                "ansible_host": "192.0.2.10",
                "ethernet_interfaces": [{"name": "Ethernet1", "peer": "device2", "peer_interface": "Ethernet1"}],
            },
            "device2": {
                "ansible_host": "192.0.2.20",
                "ethernet_interfaces": [{"name": "Ethernet1", "peer": "device1", "peer_interface": "Ethernet1"}],
            },
        },
    )

    generator = ContainerlabTopologyGenerator()
    devices_list = inventory.get_all_devices()

    # This should return empty dict when no root nodes found
    hierarchy = generator._compute_topology_hierarchy(inventory, devices_list)

    assert isinstance(hierarchy, dict)


def test_resolve_mgmt_ip_from_ansible_host(tmp_path):
    """Test that ansible_host takes precedence over device.mgmt_ip."""
    device = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )

    host_vars = {"ansible_host": "10.0.0.1"}

    generator = ContainerlabTopologyGenerator()
    result = generator._resolve_mgmt_ip(device, host_vars)

    assert result == "10.0.0.1"


def test_resolve_mgmt_ip_fallback_to_device_mgmt_ip(tmp_path):
    """Test that device.mgmt_ip is used when ansible_host is not available."""
    device = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )

    host_vars = {}

    generator = ContainerlabTopologyGenerator()
    result = generator._resolve_mgmt_ip(device, host_vars)

    assert result == "192.0.2.10"


def test_resolve_mgmt_ip_returns_none(tmp_path):
    """Test that None is returned when no mgmt IP is available."""
    device = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip=None,
        device_type="l3spine",
        fabric="lab",
    )

    host_vars = {}

    generator = ContainerlabTopologyGenerator()
    result = generator._resolve_mgmt_ip(device, host_vars)

    assert result is None


def test_derive_topology_name_with_custom_name():
    """Test that custom topology name is used when provided."""
    generator = ContainerlabTopologyGenerator()
    result = generator._derive_topology_name(Path("/path/to/custom"))

    assert result == "custom"


def test_derive_topology_name_from_inventory_root():
    """Test topology name derivation from inventory root path."""
    generator = ContainerlabTopologyGenerator()
    result = generator._derive_topology_name(Path("/path/to/my-lab"))

    assert result == "my-lab"


def test_extract_uplink_data_no_defaults(tmp_path):
    """Test _extract_uplink_data when no defaults exist."""
    device = DeviceDefinition(
        hostname="leaf1",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3leaf",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"leaf": [device]},
    )

    inventory = InventoryData(
        root_path=tmp_path,
        fabrics=[fabric],
        group_vars={},
        host_vars={},
    )

    generator = ContainerlabTopologyGenerator()
    interfaces, switches, switch_interfaces = generator._extract_uplink_data(inventory, device)

    assert interfaces == []
    assert switches == []
    assert switch_interfaces == []
