#!/usr/bin/env python
# coding: utf-8 -*-

"""Inventory loader focused on host connection resolution for deploy/info/validate."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from avd_cli.exceptions import InvalidInventoryError
from avd_cli.models.connection_inventory import (
    ConnectionInventory,
    ResolvedCredentials,
    ResolvedHostConnection,
)

logger = logging.getLogger(__name__)


class ConnectionInventoryLoader:
    """Load and normalize connection data from supported inventory schemas."""

    FLAT_SCHEMA_KEYS = {"globals", "groups", "hosts"}
    RESERVED_ANSIBLE_KEYS = {"vars", "hosts", "children"}

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def load(self, inventory_path: Path, strict: bool = True) -> ConnectionInventory:
        """Load connection inventory from a directory or inventory YAML file."""
        inventory_file = self._resolve_inventory_file(inventory_path, required=True)
        assert inventory_file is not None  # mypy/runtime guard

        data = self._load_yaml_file(inventory_file)
        schema = self.detect_schema_from_data(data)

        if schema == "flat":
            return self._parse_flat_inventory(data, strict=strict)
        return self._parse_ansible_inventory(data)

    def detect_schema(self, inventory_path: Path) -> str:
        """Detect input schema from inventory data on disk.

        Returns ``ansible`` if no inventory file exists (for compatibility with
        directory-style inventories based on group_vars/host_vars only).
        """
        inventory_file = self._resolve_inventory_file(inventory_path, required=False)
        if inventory_file is None:
            return "ansible"

        data = self._load_yaml_file(inventory_file)
        return self.detect_schema_from_data(data)

    def is_flat_schema(self, inventory_path: Path) -> bool:
        """Return True when the inventory file uses flat globals/groups/hosts format."""
        return self.detect_schema(inventory_path) == "flat"

    def detect_schema_from_data(self, data: Dict[str, Any]) -> str:
        """Detect schema based on loaded YAML data."""
        if not isinstance(data, dict):
            raise InvalidInventoryError("Inventory YAML root must be a mapping")

        has_flat_keys = any(key in data for key in self.FLAT_SCHEMA_KEYS)
        if not has_flat_keys:
            return "ansible"

        extra_keys = set(data.keys()) - self.FLAT_SCHEMA_KEYS
        if extra_keys:
            raise InvalidInventoryError(
                "Ambiguous inventory schema: flat keys (globals/groups/hosts) cannot be mixed "
                f"with other top-level keys: {', '.join(sorted(extra_keys))}"
            )

        return "flat"

    def _parse_flat_inventory(self, data: Dict[str, Any], strict: bool) -> ConnectionInventory:
        globals_data = data.get("globals", {}) or {}
        groups_data = data.get("groups", {}) or {}
        hosts_data = data.get("hosts", {}) or {}

        if not isinstance(globals_data, dict):
            raise InvalidInventoryError("Invalid flat schema: 'globals' must be a mapping")
        if not isinstance(groups_data, dict):
            raise InvalidInventoryError("Invalid flat schema: 'groups' must be a mapping")
        if not isinstance(hosts_data, dict):
            raise InvalidInventoryError("Invalid flat schema: 'hosts' must be a mapping")

        resolved_hosts = [
            self._resolve_flat_host(hostname, host_data, groups_data, globals_data, strict)
            for hostname, host_data in hosts_data.items()
        ]

        return ConnectionInventory(
            schema="flat",
            hosts=resolved_hosts,
            globals_data=globals_data,
            groups_data=groups_data,
        )

    def _resolve_flat_host(
        self,
        hostname: str,
        host_data: Any,
        groups_data: Dict[str, Any],
        globals_data: Dict[str, Any],
        strict: bool,
    ) -> ResolvedHostConnection:
        """Resolve a single host entry from flat schema data."""
        if not isinstance(host_data, dict):
            raise InvalidInventoryError(f"Host '{hostname}' must be a mapping")

        host_groups = host_data.get("groups") or []
        if not isinstance(host_groups, list) or any(not isinstance(g, str) for g in host_groups):
            raise InvalidInventoryError(f"Host '{hostname}' has invalid 'groups'. Expected a list of group names.")

        missing_groups = [g for g in host_groups if g not in groups_data]
        if missing_groups:
            raise InvalidInventoryError(
                f"Host '{hostname}' references unknown groups: {', '.join(missing_groups)}"
            )

        address = self._resolve_address(host_data)
        kind = self._resolve_kind(
            host_data=host_data, host_groups=host_groups, groups_data=groups_data, globals_data=globals_data
        )
        tls_verify = self._resolve_tls_verify(
            host_data=host_data, host_groups=host_groups, groups_data=groups_data,
            globals_data=globals_data, strict=strict,
        )
        credentials = self._resolve_credentials(
            host_data=host_data, host_groups=host_groups, groups_data=groups_data,
            globals_data=globals_data, strict=strict,
        )

        if strict and not address:
            raise InvalidInventoryError(f"Host '{hostname}' is missing address (use 'address' or 'ansible_host')")
        if strict and not kind:
            raise InvalidInventoryError(f"Host '{hostname}' is missing kind (host > groups > globals resolution)")
        if strict and credentials is None:
            raise InvalidInventoryError(
                f"Host '{hostname}' is missing complete credentials "
                "(username/password via credentials.* or ansible_user/ansible_password)"
            )

        return ResolvedHostConnection(
            hostname=hostname, address=address, groups=host_groups,
            kind=kind, credentials=credentials, tls_verify=tls_verify,
        )

    def _parse_ansible_inventory(self, data: Dict[str, Any]) -> ConnectionInventory:
        all_group = data.get("all", {}) if isinstance(data, dict) else {}
        children = all_group.get("children", {}) if isinstance(all_group, dict) else {}
        roots = children if isinstance(children, dict) and children else data

        resolved_hosts: List[ResolvedHostConnection] = []
        if not isinstance(roots, dict):
            return ConnectionInventory(schema="ansible", hosts=resolved_hosts)

        for group_name, group_data in roots.items():
            if not isinstance(group_data, dict):
                continue
            self._extract_ansible_hosts_recursive(
                group_data=group_data,
                group_name=group_name,
                parent_vars={},
                result=resolved_hosts,
            )

        return ConnectionInventory(schema="ansible", hosts=resolved_hosts)

    def _extract_ansible_hosts_recursive(
        self,
        group_data: Dict[str, Any],
        group_name: str,
        parent_vars: Dict[str, Any],
        result: List[ResolvedHostConnection],
    ) -> None:
        if not isinstance(group_data, dict):
            return

        current_vars = dict(parent_vars)
        group_vars = group_data.get("vars")
        if isinstance(group_vars, dict):
            current_vars.update(group_vars)

        hosts = group_data.get("hosts", {})
        if isinstance(hosts, dict):
            for hostname, host_data in hosts.items():
                host = self._resolve_ansible_host(hostname, host_data, group_name, current_vars)
                if host is not None:
                    result.append(host)

        self._recurse_ansible_children(group_data, current_vars, result)

    def _resolve_ansible_host(
        self,
        hostname: str,
        host_data: Any,
        group_name: str,
        current_vars: Dict[str, Any],
    ) -> Optional[ResolvedHostConnection]:
        """Resolve a single ansible-style host entry. Returns None if it should be skipped."""
        host_mapping = host_data if isinstance(host_data, dict) else {}
        address = self._resolve_address(host_mapping)
        if not address:
            self.logger.warning("Skipping %s: missing ansible_host/address", hostname)
            return None

        username, password = self._credentials_from_mapping(host_mapping)
        if not username or not password:
            group_username, group_password = self._credentials_from_mapping(current_vars)
            username = username or group_username
            password = password or group_password

        credentials: Optional[ResolvedCredentials] = None
        if username and password:
            credentials = ResolvedCredentials(username=username, password=password)

        kind = self._first_defined([host_mapping.get("kind"), current_vars.get("kind")]) or "arista_eos"
        tls_verify = self._resolve_tls_from_levels(levels=[host_mapping, current_vars], strict=False)

        return ResolvedHostConnection(
            hostname=hostname, address=address, groups=[group_name],
            kind=str(kind), credentials=credentials, tls_verify=tls_verify,
        )

    def _recurse_ansible_children(
        self,
        group_data: Dict[str, Any],
        current_vars: Dict[str, Any],
        result: List[ResolvedHostConnection],
    ) -> None:
        """Recurse into explicit 'children' and implicit nested group keys."""
        children = group_data.get("children", {})
        if isinstance(children, dict):
            for child_name, child_data in children.items():
                self._extract_ansible_hosts_recursive(
                    group_data=child_data if isinstance(child_data, dict) else {},
                    group_name=child_name,
                    parent_vars=current_vars,
                    result=result,
                )

        # Compatibility path: nested groups can appear outside "children".
        for key, value in group_data.items():
            if key in self.RESERVED_ANSIBLE_KEYS or not isinstance(value, dict):
                continue
            self._extract_ansible_hosts_recursive(
                group_data=value, group_name=key, parent_vars=current_vars, result=result
            )

    def _resolve_kind(
        self,
        host_data: Dict[str, Any],
        host_groups: List[str],
        groups_data: Dict[str, Dict[str, Any]],
        globals_data: Dict[str, Any],
    ) -> Optional[str]:
        if "kind" in host_data:
            return str(host_data["kind"])

        for group in host_groups:
            group_data = groups_data.get(group, {})
            if isinstance(group_data, dict) and "kind" in group_data:
                return str(group_data["kind"])

        if "kind" in globals_data:
            return str(globals_data["kind"])

        return None

    def _resolve_credentials(
        self,
        host_data: Dict[str, Any],
        host_groups: List[str],
        groups_data: Dict[str, Dict[str, Any]],
        globals_data: Dict[str, Any],
        strict: bool,
    ) -> Optional[ResolvedCredentials]:
        username = None
        password = None

        host_username, host_password = self._credentials_from_mapping(host_data)
        username = host_username or username
        password = host_password or password

        for group in host_groups:
            group_data = groups_data.get(group, {})
            if not isinstance(group_data, dict):
                continue

            group_username, group_password = self._credentials_from_mapping(group_data)
            if username is None and group_username is not None:
                username = group_username
            if password is None and group_password is not None:
                password = group_password

            if username is not None and password is not None:
                break

        global_username, global_password = self._credentials_from_mapping(globals_data)
        if username is None:
            username = global_username
        if password is None:
            password = global_password

        if strict:
            self._assert_string_or_none(username, "credentials.username")
            self._assert_string_or_none(password, "credentials.password")

        if username is None or password is None:
            return None
        return ResolvedCredentials(username=str(username), password=str(password))

    def _resolve_tls_verify(
        self,
        host_data: Dict[str, Any],
        host_groups: List[str],
        groups_data: Dict[str, Dict[str, Any]],
        globals_data: Dict[str, Any],
        strict: bool,
    ) -> Optional[bool]:
        levels: List[Dict[str, Any]] = [host_data]
        for group in host_groups:
            group_data = groups_data.get(group, {})
            if isinstance(group_data, dict):
                levels.append(group_data)
        levels.append(globals_data)
        return self._resolve_tls_from_levels(levels=levels, strict=strict)

    def _resolve_tls_from_levels(self, levels: List[Dict[str, Any]], strict: bool) -> Optional[bool]:
        for level in levels:
            if not isinstance(level, dict):
                continue

            if "tls_verify" in level:
                return self._coerce_bool(level["tls_verify"], "tls_verify", strict)
            if "ansible_httpapi_validate_certs" in level:
                key = "ansible_httpapi_validate_certs"
                return self._coerce_bool(level[key], key, strict)
        return None

    def _resolve_address(self, data: Dict[str, Any]) -> Optional[str]:
        address = data.get("address")
        if address is None:
            address = data.get("ansible_host")
        if address is None:
            return None
        return str(address)

    def _credentials_from_mapping(self, data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        credentials = data.get("credentials")
        username = None
        password = None

        if isinstance(credentials, dict):
            username = credentials.get("username")
            password = credentials.get("password")

        if username is None:
            username = data.get("ansible_user")
        if password is None:
            password = data.get("ansible_password")

        if username is not None:
            username = str(username)
        if password is not None:
            password = str(password)
        return username, password

    def _coerce_bool(self, value: Any, field_name: str, strict: bool) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "1", "on"}:
                return True
            if lowered in {"false", "no", "0", "off"}:
                return False
        if strict:
            raise InvalidInventoryError(f"Field '{field_name}' must be a boolean")
        return None

    def _assert_string_or_none(self, value: Any, field_name: str) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise InvalidInventoryError(f"Field '{field_name}' must be a string")

    def _first_defined(self, values: List[Any]) -> Optional[Any]:
        for value in values:
            if value is not None:
                return value
        return None

    def _resolve_inventory_file(self, inventory_path: Path, required: bool) -> Optional[Path]:
        if inventory_path.is_file():
            return inventory_path

        if not inventory_path.exists():
            if required:
                raise InvalidInventoryError(f"Inventory path does not exist: {inventory_path}")
            return None

        if not inventory_path.is_dir():
            raise InvalidInventoryError(f"Inventory path is not a directory: {inventory_path}")

        inventory_file = inventory_path / "inventory.yml"
        if inventory_file.exists():
            return inventory_file

        inventory_file = inventory_path / "inventory.yaml"
        if inventory_file.exists():
            return inventory_file

        if required:
            raise InvalidInventoryError(
                f"No inventory.yml or inventory.yaml found in {inventory_path}"
            )
        return None

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as stream:
                loaded = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise InvalidInventoryError(f"Invalid YAML in {file_path}: {exc}") from exc
        except OSError as exc:
            raise InvalidInventoryError(f"Cannot read inventory file {file_path}: {exc}") from exc

        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise InvalidInventoryError(f"Inventory file {file_path} must contain a YAML mapping")
        return loaded
