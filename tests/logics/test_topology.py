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
        topology_name="lab-topology",
    )

    assert result.topology_path.exists()
    payload = yaml.safe_load(result.topology_path.read_text(encoding="utf-8"))

    assert payload["name"] == "lab-topology"
    nodes = payload["topology"]["nodes"]
    assert "spine1" in nodes
    assert nodes["spine1"]["labels"]["graph-level"] == 0
    assert nodes["leaf1"]["labels"]["graph-level"] == 1

    links = payload["topology"]["links"]
    assert len(links) == 1
    endpoints = links[0]["endpoints"]
    assert "spine1:Ethernet1" in endpoints
    assert "leaf1:Ethernet49" in endpoints
