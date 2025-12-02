from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import yaml

from avd_cli.models.inventory import DeviceDefinition, InventoryData

logger = logging.getLogger(__name__)


@dataclass
class ContainerlabTopologyGenerationResult:
    """Result metadata produced after topology generation."""

    topology_path: Path
    nodes: Dict[str, Dict[str, Any]]
    links: List[Dict[str, Any]]


class ContainerlabTopologyGenerator:
    """Generate Containerlab topology definitions from resolved AVD inventory."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate(
        self,
        inventory: InventoryData,
        output_path: Path,
        device_filter: Optional[Any] = None,
        startup_dir: Path | str | None = None,
        node_kind: str = "ceos",
        topology_name: str = "containerlab-topology",
    ) -> ContainerlabTopologyGenerationResult:
        """Build Containerlab topology from inventory and write to disk."""

        devices = self._filter_devices(inventory, device_filter)
        startup_dir = self._normalize_startup_dir(inventory.root_path, startup_dir)
        node_data = self._build_nodes(inventory, devices, startup_dir, node_kind)
        links = self._build_links(inventory, devices)
        defaults = self._extract_defaults(inventory)

        topology = {
            "name": topology_name,
            "topology": {
                "defaults": defaults,
                "nodes": node_data,
                "links": links,
            },
        }

        containerlab_dir = output_path / "containerlab"
        containerlab_dir.mkdir(parents=True, exist_ok=True)
        topology_path = containerlab_dir / f"{topology_name}.yml"
        with topology_path.open("w", encoding="utf-8") as topology_file:
            yaml.safe_dump(topology, topology_file, sort_keys=False)

        return ContainerlabTopologyGenerationResult(topology_path=topology_path, nodes=node_data, links=links)

    def _filter_devices(self, inventory: InventoryData, device_filter: Optional[Any]) -> List[DeviceDefinition]:
        devices = inventory.get_all_devices()
        if not device_filter:
            return devices

        filtered = [
            device
            for device in devices
            if device_filter.matches_device(device.hostname, device.groups + [device.fabric])
        ]
        self.logger.info("Filtering topology to %d devices", len(filtered))
        return filtered

    def _normalize_startup_dir(self, root_path: Path, startup_dir: Path | str | None) -> Path:
        if startup_dir is None:
            return root_path / "intended" / "configs"
        startup_path = Path(startup_dir)
        return startup_path if startup_path.is_absolute() else root_path / startup_path

    def _extract_defaults(self, inventory: InventoryData) -> Dict[str, Any]:
        for group_vars in inventory.group_vars.values():
            for design in ("l2leaf", "l3leaf", "leaf", "spine"):
                topology = group_vars.get(design)
                if isinstance(topology, dict):
                    defaults = topology.get("defaults")
                    if isinstance(defaults, dict) and defaults:
                        return defaults
        return {}

    def _build_nodes(
        self,
        inventory: InventoryData,
        devices: Iterable[DeviceDefinition],
        startup_dir: Path,
        node_kind: str,
    ) -> Dict[str, Dict[str, Any]]:
        nodes: Dict[str, Dict[str, Any]] = {}
        for device in devices:
            host_vars = inventory.host_vars.get(device.hostname, {})
            mgmt_ip = self._resolve_mgmt_ip(device, host_vars)
            if not mgmt_ip:
                self.logger.warning("Skipping device %s because mgmt IP could not be resolved", device.hostname)
                continue

            node_config = {
                "kind": node_kind,
                "mgmt-ipv4": mgmt_ip,
                "startup-config": str((startup_dir / f"{device.hostname}.cfg").as_posix()),
                "labels": {
                    "graph-level": self._graph_level(device),
                    "graph-icon": "router",
                },
            }
            nodes[device.hostname] = node_config
        return nodes

    def _build_links(self, inventory: InventoryData, devices: Iterable[DeviceDefinition]) -> List[Dict[str, Any]]:
        links: List[Dict[str, Any]] = []
        seen: Set[tuple[str, str]] = set()
        valid_hosts = {device.hostname for device in devices}
        for device in devices:
            host_vars = inventory.host_vars.get(device.hostname, {})
            ethernet_interfaces = host_vars.get("ethernet_interfaces", []) or []
            for interface in ethernet_interfaces:
                name = interface.get("name")
                peer = interface.get("peer")
                peer_interface = interface.get("peer_interface")
                if not name or not peer or not peer_interface:
                    continue
                if peer not in valid_hosts:
                    continue

                endpoint_a = f"{device.hostname}:{name}"
                endpoint_b = f"{peer}:{peer_interface}"
                key = tuple(sorted((endpoint_a, endpoint_b)))
                if key in seen:
                    continue
                seen.add(key)

                link: Dict[str, Any] = {"endpoints": [endpoint_a, endpoint_b]}
                description = interface.get("description")
                if description:
                    link["description"] = description
                links.append(link)
        return links

    def _resolve_mgmt_ip(self, device: DeviceDefinition, host_vars: Dict[str, Any]) -> Optional[str]:
        ansible_host = host_vars.get("ansible_host")
        if ansible_host:
            return str(ansible_host)
        mgmt_ip = device.mgmt_ip
        return str(mgmt_ip) if mgmt_ip else None

    def _graph_level(self, device: DeviceDefinition) -> int:
        device_type = (device.device_type or "").lower()
        if "spine" in device_type:
            return 0
        if "leaf" in device_type:
            return 1
        return 2
