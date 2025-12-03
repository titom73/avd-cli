from pathlib import Path

import yaml

from avd_cli.logics.topology import ContainerlabTopologyGenerator
from avd_cli.models.inventory import DeviceDefinition, FabricDefinition, InventoryData


def _create_inventory_structure(root_path: Path) -> InventoryData:
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

    return InventoryData(
        root_path=root_path,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "platform": "cEOS",
                        "loopback_ipv4_pool": "192.0.255.0/24",
                    }
                }
            }
        },
        host_vars={
            "spine1": {
                "ansible_host": "192.168.0.1",
                "ethernet_interfaces": [
                    {
                        "name": "Ethernet1",
                        "peer": "leaf1",
                        "peer_interface": "Ethernet49",
                        "description": "uplink",
                    }
                ],
            },
            "leaf1": {
                "ansible_host": "192.168.0.2",
                "ethernet_interfaces": [
                    {
                        "name": "Ethernet49",
                        "peer": "spine1",
                        "peer_interface": "Ethernet1",
                    }
                ],
            },
        },
    )


def test_containerlab_topology_generator(tmp_path: Path) -> None:
    inventory_root = tmp_path / "inventory"
    inventory_root.mkdir(parents=True, exist_ok=True)
    inventory = _create_inventory_structure(inventory_root)

    generator = ContainerlabTopologyGenerator()
    result = generator.generate(
        inventory,
        tmp_path,
        device_filter=None,
        startup_dir=inventory_root / "intended" / "configs",
        node_kind="ceos",
        node_image="arista/ceos:latest",
        topology_name="lab-topology",
    )

    assert result.topology_path.exists()
    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))

    assert payload["name"] == "lab-topology"
    nodes = payload["topology"]["nodes"]
    assert "spine1" in nodes
    assert "leaf1" in nodes

    links = payload["topology"]["links"]
    assert len(links) == 1
    endpoints = links[0]["endpoints"]
    assert "spine1:Ethernet1" in endpoints
    assert "leaf1:Ethernet49" in endpoints


def test_containerlab_topology_with_uplinks(tmp_path: Path) -> None:
    """Test topology generation with uplink-based links from AVD structure."""
    inventory_root = tmp_path / "inventory"
    inventory_root.mkdir(parents=True, exist_ok=True)

    spine1 = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="lab",
    )
    spine2 = DeviceDefinition(
        hostname="spine2",
        platform="ceos",
        mgmt_ip="192.0.2.11",
        device_type="l3spine",
        fabric="lab",
    )
    leaf1 = DeviceDefinition(
        hostname="leaf1",
        platform="ceos",
        mgmt_ip="192.0.2.20",
        device_type="l3leaf",
        fabric="lab",
    )

    fabric = FabricDefinition(
        name="lab",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [spine1, spine2], "leaf": [leaf1]},
    )

    inventory = InventoryData(
        root_path=inventory_root,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "platform": "cEOS",
                        "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                        "uplink_switches": ["spine1", "spine2"],
                    },
                    "node_groups": [
                        {
                            "group": "pod1",
                            "nodes": [
                                {
                                    "name": "leaf1",
                                    "uplink_switch_interfaces": ["Ethernet10", "Ethernet10"],
                                }
                            ],
                        }
                    ],
                }
            }
        },
        host_vars={
            "spine1": {"ansible_host": "192.168.0.1"},
            "spine2": {"ansible_host": "192.168.0.2"},
            "leaf1": {"ansible_host": "192.168.0.10"},
        },
    )

    generator = ContainerlabTopologyGenerator()
    result = generator.generate(
        inventory,
        tmp_path,
        device_filter=None,
        startup_dir=inventory_root / "configs",
        node_kind="ceos",
        node_image="arista/ceos:latest",
        topology_name="uplink-topology",
    )

    assert result.topology_path.exists()
    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))

    links = payload["topology"]["links"]
    assert len(links) == 2

    endpoints_set = {tuple(sorted(link["endpoints"])) for link in links}
    assert ("leaf1:Ethernet1", "spine1:Ethernet10") in endpoints_set
    assert ("leaf1:Ethernet2", "spine2:Ethernet10") in endpoints_set


def test_containerlab_topology_uplink_deduplication(tmp_path: Path) -> None:
    """Test that uplink-based links are deduplicated with ethernet_interfaces links."""
    inventory_root = tmp_path / "inventory"
    inventory_root.mkdir(parents=True, exist_ok=True)

    spine1 = DeviceDefinition(
        hostname="spine1", platform="ceos", mgmt_ip="192.0.2.10", device_type="l3spine", fabric="lab"
    )
    leaf1 = DeviceDefinition(
        hostname="leaf1", platform="ceos", mgmt_ip="192.0.2.20", device_type="l3leaf", fabric="lab"
    )

    fabric = FabricDefinition(
        name="lab", design_type="l3ls-evpn", devices_by_type={"spine": [spine1], "leaf": [leaf1]}
    )

    inventory = InventoryData(
        root_path=inventory_root,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "uplink_interfaces": ["Ethernet1"],
                        "uplink_switches": ["spine1"],
                    },
                    "node_groups": [
                        {
                            "group": "pod1",
                            "nodes": [{"name": "leaf1", "uplink_switch_interfaces": ["Ethernet10"]}],
                        }
                    ],
                }
            }
        },
        host_vars={
            "spine1": {
                "ansible_host": "192.168.0.1",
                "ethernet_interfaces": [
                    {"name": "Ethernet10", "peer": "leaf1", "peer_interface": "Ethernet1"}
                ],
            },
            "leaf1": {
                "ansible_host": "192.168.0.10",
                "ethernet_interfaces": [
                    {"name": "Ethernet1", "peer": "spine1", "peer_interface": "Ethernet10"}
                ],
            },
        },
    )

    generator = ContainerlabTopologyGenerator()
    result = generator.generate(
        inventory, tmp_path, device_filter=None, node_kind="ceos", node_image="arista/ceos:latest"
    )

    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))
    links = payload["topology"]["links"]

    assert len(links) == 1, "Link should be deduplicated between ethernet_interfaces and uplink structure"
    assert links[0]["endpoints"] == ["leaf1:Ethernet1", "spine1:Ethernet10"] or links[0]["endpoints"] == [
        "spine1:Ethernet10",
        "leaf1:Ethernet1",
    ]


def test_containerlab_topology_dynamic_hierarchy(tmp_path: Path) -> None:
    """Test dynamic hierarchy computation based on uplink topology analysis."""
    inventory_root = tmp_path / "inventory"
    inventory_root.mkdir(parents=True, exist_ok=True)

    spine1 = DeviceDefinition(
        hostname="spine1", platform="ceos", mgmt_ip="192.0.2.10", device_type="l3spine", fabric="lab"
    )
    spine2 = DeviceDefinition(
        hostname="spine2", platform="ceos", mgmt_ip="192.0.2.11", device_type="l3spine", fabric="lab"
    )
    leaf1 = DeviceDefinition(
        hostname="leaf1", platform="ceos", mgmt_ip="192.0.2.20", device_type="l3leaf", fabric="lab"
    )
    leaf2 = DeviceDefinition(
        hostname="leaf2", platform="ceos", mgmt_ip="192.0.2.21", device_type="l3leaf", fabric="lab"
    )

    fabric = FabricDefinition(
        name="lab", design_type="l3ls-evpn", devices_by_type={"spine": [spine1, spine2], "leaf": [leaf1, leaf2]}
    )

    inventory = InventoryData(
        root_path=inventory_root,
        fabrics=[fabric],
        group_vars={
            "lab": {
                "l3leaf": {
                    "defaults": {
                        "platform": "cEOS",
                        "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                        "uplink_switches": ["spine1", "spine2"],
                    },
                    "node_groups": [
                        {
                            "group": "pod1",
                            "nodes": [
                                {"name": "leaf1", "uplink_switch_interfaces": ["Ethernet10", "Ethernet11"]},
                                {"name": "leaf2", "uplink_switch_interfaces": ["Ethernet12", "Ethernet13"]},
                            ],
                        }
                    ],
                }
            }
        },
        host_vars={
            "spine1": {"ansible_host": "192.168.0.1"},
            "spine2": {"ansible_host": "192.168.0.2"},
            "leaf1": {"ansible_host": "192.168.0.10"},
            "leaf2": {"ansible_host": "192.168.0.11"},
        },
    )

    generator = ContainerlabTopologyGenerator()
    result = generator.generate(
        inventory, tmp_path, device_filter=None, node_kind="ceos", node_image="arista/ceos:latest"
    )

    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))
    nodes = payload["topology"]["nodes"]

    spine1_level = nodes["spine1"]["labels"]["graph-level"]
    spine2_level = nodes["spine2"]["labels"]["graph-level"]
    leaf1_level = nodes["leaf1"]["labels"]["graph-level"]
    leaf2_level = nodes["leaf2"]["labels"]["graph-level"]

    # Spines (no uplinks, depth=0) should have higher graph-level than leafs (uplinks to spines, depth=1)
    assert spine1_level > leaf1_level, f"spine1 ({spine1_level}) should have higher level than leaf1 ({leaf1_level})"
    assert spine2_level > leaf2_level, f"spine2 ({spine2_level}) should have higher level than leaf2 ({leaf2_level})"
    
    # Spines should have same level (both depth=0)
    assert spine1_level == spine2_level, "Both spines should have same graph-level"
    
    # Leafs should have same level (both depth=1)
    assert leaf1_level == leaf2_level, "Both leafs should have same graph-level"


def test_containerlab_topology_custom_image(tmp_path: Path) -> None:
    """Test topology generation with custom Docker image configurations."""
    inventory_root = tmp_path / "inventory"
    inventory_root.mkdir(parents=True, exist_ok=True)

    spine = DeviceDefinition(
        hostname="spine1",
        platform="ceos",
        mgmt_ip="192.0.2.10",
        device_type="l3spine",
        fabric="test",
    )

    fabric = FabricDefinition(
        name="test",
        design_type="l3ls-evpn",
        devices_by_type={"spine": [spine]},
    )

    inventory = InventoryData(
        root_path=inventory_root,
        fabrics=[fabric],
        group_vars={},
        host_vars={"spine1": {"ansible_host": "192.168.1.1"}},
    )

    generator = ContainerlabTopologyGenerator()

    # Test with custom complete image
    result = generator.generate(
        inventory,
        tmp_path,
        device_filter=None,
        node_kind="ceos",
        node_image="ghcr.io/aristanetworks/ceos:4.32.0F",
        topology_name="custom-image",
    )

    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))
    nodes = payload["topology"]["nodes"]

    assert "spine1" in nodes
    assert nodes["spine1"]["kind"] == "ceos"
    assert nodes["spine1"]["image"] == "ghcr.io/aristanetworks/ceos:4.32.0F"

    # Test with different kind and image
    result2 = generator.generate(
        inventory,
        tmp_path,
        device_filter=None,
        node_kind="vr-arista_veos",
        node_image="vrnetlab/vr-arista_veos:4.32.0F",
        topology_name="vrnetlab-topology",
    )

    payload2 = yaml.safe_load(result2.topology_path.read_text(encoding="utf-8"))
    nodes2 = payload2["topology"]["nodes"]

    assert nodes2["spine1"]["kind"] == "vr-arista_veos"
    assert nodes2["spine1"]["image"] == "vrnetlab/vr-arista_veos:4.32.0F"

