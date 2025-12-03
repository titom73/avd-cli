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
        node_image: str = "arista/ceos:latest",
        topology_name: str = "containerlab-topology",
    ) -> ContainerlabTopologyGenerationResult:
        """Build Containerlab topology from inventory and write to disk."""

        devices = self._filter_devices(inventory, device_filter)
        startup_dir = self._normalize_startup_dir(output_path, startup_dir)

        containerlab_dir = output_path / "containerlab"
        containerlab_dir.mkdir(parents=True, exist_ok=True)
        topology_path = containerlab_dir / f"{topology_name}.yml"

        node_data = self._build_nodes(inventory, devices, startup_dir, node_kind, node_image, topology_path)
        links = self._build_links(inventory, devices)

        topology = {
            "name": topology_name,
            "topology": {
                "nodes": node_data,
                "links": links,
            },
        }

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
            return root_path / "configs"
        startup_path = Path(startup_dir)
        return startup_path if startup_path.is_absolute() else root_path / startup_path

    def _build_nodes(
        self,
        inventory: InventoryData,
        devices: Iterable[DeviceDefinition],
        startup_dir: Path,
        node_kind: str,
        node_image: str,
        topology_path: Path,
    ) -> Dict[str, Dict[str, Any]]:
        devices_list = list(devices)
        hierarchy = self._compute_topology_hierarchy(inventory, devices_list)

        nodes: Dict[str, Dict[str, Any]] = {}
        for device in devices_list:
            host_vars = inventory.host_vars.get(device.hostname, {})
            mgmt_ip = self._resolve_mgmt_ip(device, host_vars)
            if not mgmt_ip:
                self.logger.warning("Skipping device %s because mgmt IP could not be resolved", device.hostname)
                continue

            startup_config_path = startup_dir / f"{device.hostname}.cfg"
            relative_path = self._compute_relative_path(topology_path, startup_config_path)

            node_config = {
                "kind": node_kind,
                "image": node_image,
                "mgmt-ipv4": mgmt_ip,
                "startup-config": relative_path,
                "labels": {
                    "graph-level": self._graph_level(device, hierarchy),
                    "graph-icon": "router",
                },
            }
            nodes[device.hostname] = node_config
        return nodes

    def _extract_uplink_data(
        self, inventory: InventoryData, device: DeviceDefinition
    ) -> tuple[List[str], List[str], List[str]]:
        """Extract uplink topology from AVD group_vars structure for a device."""
        for group_vars in inventory.group_vars.values():
            for layer_key in ("l3leaf", "l2leaf"):
                layer_config = group_vars.get(layer_key)
                if not isinstance(layer_config, dict):
                    continue

                defaults = layer_config.get("defaults", {})
                uplink_interfaces_default = defaults.get("uplink_interfaces", [])
                uplink_switches_default = defaults.get("uplink_switches", [])

                node_groups = layer_config.get("node_groups", [])
                for node_group in node_groups:
                    if not isinstance(node_group, dict):
                        continue

                    nodes = node_group.get("nodes", [])
                    for node in nodes:
                        if not isinstance(node, dict):
                            continue
                        if node.get("name") != device.hostname:
                            continue

                        uplink_switch_interfaces = node.get("uplink_switch_interfaces", [])
                        uplink_interfaces = node.get("uplink_interfaces", uplink_interfaces_default)
                        uplink_switches = node.get("uplink_switches", uplink_switches_default)

                        return uplink_interfaces, uplink_switches, uplink_switch_interfaces

        return [], [], []

    def _build_links(self, inventory: InventoryData, devices: Iterable[DeviceDefinition]) -> List[Dict[str, Any]]:
        links: List[Dict[str, Any]] = []
        seen: Set[tuple[str, str]] = set()
        valid_hosts = {device.hostname for device in devices}

        for device in devices:
            host_vars = inventory.host_vars.get(device.hostname, {})

            # Source 1: ethernet_interfaces with peer information
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

            # Source 2: uplink topology from AVD structure
            uplink_interfaces, uplink_switches, uplink_switch_interfaces = self._extract_uplink_data(inventory, device)

            if uplink_interfaces and uplink_switches and uplink_switch_interfaces:
                if not (len(uplink_interfaces) == len(uplink_switches) == len(uplink_switch_interfaces)):
                    self.logger.warning(
                        "Device %s has mismatched uplink array lengths: "
                        "interfaces=%d, switches=%d, switch_interfaces=%d",
                        device.hostname,
                        len(uplink_interfaces),
                        len(uplink_switches),
                        len(uplink_switch_interfaces),
                    )
                    continue

                for local_intf, uplink_switch, uplink_intf in zip(
                    uplink_interfaces, uplink_switches, uplink_switch_interfaces
                ):
                    if uplink_switch not in valid_hosts:
                        continue

                    endpoint_a = f"{device.hostname}:{local_intf}"
                    endpoint_b = f"{uplink_switch}:{uplink_intf}"
                    key = tuple(sorted((endpoint_a, endpoint_b)))
                    if key in seen:
                        continue
                    seen.add(key)

                    link: Dict[str, Any] = {"endpoints": [endpoint_a, endpoint_b]}
                    links.append(link)

        return links

    def _resolve_mgmt_ip(self, device: DeviceDefinition, host_vars: Dict[str, Any]) -> Optional[str]:
        ansible_host = host_vars.get("ansible_host")
        if ansible_host:
            return str(ansible_host)
        mgmt_ip = device.mgmt_ip
        return str(mgmt_ip) if mgmt_ip else None

    def _compute_relative_path(self, from_path: Path, to_path: Path) -> str:
        """Compute relative path from topology file to startup config.

        Args:
            from_path: Path to the topology YAML file
            to_path: Path to the startup config file

        Returns:
            Relative path as POSIX string
        """
        try:
            from_resolved = from_path.resolve()
            to_resolved = to_path.resolve()
            relative = to_resolved.relative_to(from_resolved.parent)
            return relative.as_posix()
        except ValueError:
            import os
            from_resolved = from_path.resolve()
            to_resolved = to_path.resolve()
            rel_path = os.path.relpath(to_resolved, from_resolved.parent)
            return Path(rel_path).as_posix()

    def _compute_topology_hierarchy(
        self, inventory: InventoryData, devices: List[DeviceDefinition]
    ) -> Dict[str, int]:
        """Compute network hierarchy by analyzing uplink relationships.

        Builds a directed graph where edges represent parent-child relationships
        (child has uplink to parent). Computes depth of each device from root nodes
        (devices with no uplinks).

        Returns:
            Dict mapping device hostname to its depth (0=core/spine, 1=leaf, 2=access, etc.)
        """
        valid_hostnames = {device.hostname for device in devices}
        children_to_parents: Dict[str, Set[str]] = {hostname: set() for hostname in valid_hostnames}

        for device in devices:
            _, uplink_switches, _ = self._extract_uplink_data(inventory, device)
            for parent in uplink_switches:
                if parent in valid_hostnames:
                    children_to_parents[device.hostname].add(parent)

            host_vars = inventory.host_vars.get(device.hostname, {})
            ethernet_interfaces = host_vars.get("ethernet_interfaces", []) or []
            for interface in ethernet_interfaces:
                peer = interface.get("peer")
                if peer and peer in valid_hostnames:
                    if self._is_uplink_peer(device.hostname, peer, inventory):
                        children_to_parents[device.hostname].add(peer)

        device_depths: Dict[str, int] = {}
        root_nodes = [hostname for hostname, parents in children_to_parents.items() if not parents]

        if not root_nodes:
            self.logger.warning("No root nodes found in topology (all devices have uplinks). Using device types as fallback.")
            return {}

        visited: Set[str] = set()
        queue: List[tuple[str, int]] = [(node, 0) for node in root_nodes]

        while queue:
            current, depth = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            device_depths[current] = depth

            for child, parents in children_to_parents.items():
                if current in parents and child not in visited:
                    queue.append((child, depth + 1))

        for hostname in valid_hostnames:
            if hostname not in device_depths:
                device_depths[hostname] = 0

        return device_depths

    def _is_uplink_peer(self, device_hostname: str, peer_hostname: str, inventory: InventoryData) -> bool:
        """Determine if peer connection represents an uplink (device→peer is child→parent).

        Uses heuristics: if device has uplinks defined and peer doesn't, peer is likely parent.
        """
        device_obj = next((d for d in inventory.get_all_devices() if d.hostname == device_hostname), None)
        peer_obj = next((d for d in inventory.get_all_devices() if d.hostname == peer_hostname), None)

        if not device_obj or not peer_obj:
            return False

        _, device_uplinks, _ = self._extract_uplink_data(inventory, device_obj)
        _, peer_uplinks, _ = self._extract_uplink_data(inventory, peer_obj)

        if device_uplinks and not peer_uplinks:
            return True
        if peer_hostname in device_uplinks:
            return True
        return False

    def _graph_level(self, device: DeviceDefinition, hierarchy: Dict[str, int]) -> int:
        """Compute Containerlab graph-level from topology hierarchy.

        Uses computed depth where 0=core/root. Inverts so higher tier devices
        get higher graph-level values for proper visualization.

        Args:
            device: Device definition
            hierarchy: Dict mapping hostname to depth (0=core, 1=distribution, etc.)

        Returns:
            Graph level (1-9, where 9 is topmost)
        """
        if device.hostname in hierarchy:
            max_depth = max(hierarchy.values()) if hierarchy else 0
            depth = hierarchy[device.hostname]
            return max_depth - depth + 1

        device_type = (device.device_type or "").lower()
        if "spine" in device_type or "core" in device_type or device_type == "p":
            return 9
        if "leaf" in device_type or device_type in ("pe", "border"):
            return 5
        return 5
