#!/usr/bin/env python
# coding: utf-8 -*-

"""Inventory loader that resolves host connection data from Ansible-standard inventories."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from avd_cli.exceptions import InvalidInventoryError
from avd_cli.models.connection_inventory import (
    ConnectionInventory,
    ResolvedCredentials,
    ResolvedHostConnection,
)

logger = logging.getLogger(__name__)

# ansible_network_os value that identifies Arista EOS devices
_ARISTA_EOS_NETWORK_OS = "arista.eos.eos"

# Keys that delimit a group entry — not themselves sub-groups
_RESERVED_GROUP_KEYS = {"vars", "hosts", "children"}


class ConnectionInventoryLoader:
    """Resolve per-host connection data from a standard Ansible inventory file.

    Reads ``inventory.yml`` (or ``inventory.yaml``) under the supplied path and
    extracts the variables needed by ``deploy eos``, ``info``, and ``validate``:

    - ``ansible_host``               — IP address / FQDN (required)
    - ``ansible_user``               — eAPI username (required)
    - ``ansible_password``           — eAPI password (required)
    - ``ansible_network_os``         — device OS; only ``arista.eos.eos`` hosts
                                       are included; absent → treated as EOS
    - ``ansible_httpapi_validate_certs`` — SSL certificate validation (optional)
    - ``ansible_httpapi_use_ssl``    — must be ``true``; ``false`` triggers a
                                       warning because HTTP eAPI is not supported

    Variable precedence follows Ansible conventions: host variables override
    group variables, which override parent-group variables.  A host that appears
    under multiple ``children`` references is deduplicated; the first resolved
    connection data is kept and group memberships are accumulated.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, inventory_path: Path) -> ConnectionInventory:
        """Load and resolve all host connections from an Ansible inventory.

        Parameters
        ----------
        inventory_path : Path
            Path to an inventory file **or** a directory containing
            ``inventory.yml`` / ``inventory.yaml``.

        Returns
        -------
        ConnectionInventory
            Resolved host connections ready for use by deployment commands.

        Raises
        ------
        InvalidInventoryError
            If the inventory file is missing, malformed, or contains
            unresolvable references.
        """
        inventory_file = self._resolve_inventory_file(inventory_path, required=True)
        assert inventory_file is not None  # mypy guard
        data = self._load_yaml_file(inventory_file)
        return self._parse_ansible_inventory(data)

    # ------------------------------------------------------------------
    # Ansible inventory parsing
    # ------------------------------------------------------------------

    def _parse_ansible_inventory(self, data: Dict[str, Any]) -> ConnectionInventory:
        """Parse a top-level Ansible inventory mapping into resolved hosts."""
        if not isinstance(data, dict):
            raise InvalidInventoryError("Inventory YAML root must be a mapping")

        # Standard Ansible layout: all.vars + all.children
        all_group = data.get("all", {}) if isinstance(data, dict) else {}
        all_vars: Dict[str, Any] = {}
        if isinstance(all_group, dict):
            raw_vars = all_group.get("vars")
            if isinstance(raw_vars, dict):
                all_vars = raw_vars

        children = all_group.get("children", {}) if isinstance(all_group, dict) else {}
        roots = children if isinstance(children, dict) and children else data

        # seen tracks hostname → ResolvedHostConnection for deduplication.
        # When a host appears under multiple parent groups (e.g. ATD_LEAFS
        # referenced under ATD_FABRIC, ATD_TENANTS_NETWORKS, ATD_SERVERS),
        # connection data from the first encounter is kept; subsequent
        # encounters only append new group names.
        seen: Dict[str, ResolvedHostConnection] = {}

        if isinstance(roots, dict):
            for group_name, group_data in roots.items():
                if not isinstance(group_data, dict):
                    continue
                self._extract_hosts_recursive(
                    group_data=group_data,
                    group_name=group_name,
                    parent_vars=all_vars,
                    seen=seen,
                )

        return ConnectionInventory(hosts=list(seen.values()))

    def _extract_hosts_recursive(
        self,
        group_data: Dict[str, Any],
        group_name: str,
        parent_vars: Dict[str, Any],
        seen: Dict[str, ResolvedHostConnection],
    ) -> None:
        """Walk a group tree depth-first, resolving hosts along the way."""
        if not isinstance(group_data, dict):
            return

        # Merge group vars on top of inherited vars (child wins over parent)
        effective_vars = dict(parent_vars)
        raw_vars = group_data.get("vars")
        if isinstance(raw_vars, dict):
            effective_vars.update(raw_vars)

        # Process hosts declared directly in this group
        hosts = group_data.get("hosts", {})
        if isinstance(hosts, dict):
            for hostname, host_data in hosts.items():
                self._register_host(hostname, host_data, group_name, effective_vars, seen)

        # Recurse into children
        self._recurse_children(group_data, effective_vars, seen)

    def _register_host(
        self,
        hostname: str,
        host_data: Any,
        group_name: str,
        effective_vars: Dict[str, Any],
        seen: Dict[str, ResolvedHostConnection],
    ) -> None:
        """Add a host to *seen*, or merge group membership if already present."""
        if hostname in seen:
            # Host already resolved from a previous group traversal path.
            # Only accumulate the new group name to record full membership.
            existing = seen[hostname]
            if group_name not in existing.groups:
                existing.groups.append(group_name)
            return

        resolved = self._resolve_host(hostname, host_data, group_name, effective_vars)
        if resolved is not None:
            seen[hostname] = resolved

    def _resolve_host(
        self,
        hostname: str,
        host_data: Any,
        group_name: str,
        effective_vars: Dict[str, Any],
    ) -> Optional[ResolvedHostConnection]:
        """Build a ResolvedHostConnection for one host.  Returns None to skip."""
        host_mapping: Dict[str, Any] = host_data if isinstance(host_data, dict) else {}

        # Merge: effective_vars (group chain) ← host_mapping (host wins)
        merged: Dict[str, Any] = {**effective_vars, **host_mapping}

        address = self._resolve_address(merged)
        if not address:
            self.logger.warning("Skipping %s: ansible_host not set", hostname)
            return None

        kind = self._resolve_network_os(hostname, merged)
        if kind is None:
            # Non-EOS device — skip silently (warning already logged)
            return None

        credentials = self._resolve_credentials(hostname, merged)
        tls_verify = self._resolve_tls_verify(merged)

        return ResolvedHostConnection(
            hostname=hostname,
            address=address,
            groups=[group_name],
            kind=kind,
            credentials=credentials,
            tls_verify=tls_verify,
        )

    def _recurse_children(
        self,
        group_data: Dict[str, Any],
        effective_vars: Dict[str, Any],
        seen: Dict[str, ResolvedHostConnection],
    ) -> None:
        """Recurse into explicit ``children`` and implicit nested group keys."""
        children = group_data.get("children", {})
        if isinstance(children, dict):
            for child_name, child_data in children.items():
                self._extract_hosts_recursive(
                    group_data=child_data if isinstance(child_data, dict) else {},
                    group_name=child_name,
                    parent_vars=effective_vars,
                    seen=seen,
                )

        # Some inventories nest groups directly without an explicit "children" key
        for key, value in group_data.items():
            if key in _RESERVED_GROUP_KEYS or not isinstance(value, dict):
                continue
            self._extract_hosts_recursive(
                group_data=value,
                group_name=key,
                parent_vars=effective_vars,
                seen=seen,
            )

    # ------------------------------------------------------------------
    # Per-variable resolution helpers
    # ------------------------------------------------------------------

    def _resolve_network_os(self, hostname: str, merged: Dict[str, Any]) -> Optional[str]:
        """Derive the internal ``kind`` from ``ansible_network_os``.

        Returns
        -------
        str
            ``"arista_eos"`` when the host should be deployed.
        None
            When ``ansible_network_os`` is explicitly set to a non-EOS value;
            the host is skipped with a warning.
        """
        network_os = merged.get("ansible_network_os")
        if network_os is None:
            # Variable absent: assume EOS for backward compatibility
            return "arista_eos"

        if str(network_os).strip().lower() == _ARISTA_EOS_NETWORK_OS:
            return "arista_eos"

        self.logger.warning(
            "Skipping %s: ansible_network_os='%s' is not supported by 'deploy eos' "
            "(expected '%s')",
            hostname,
            network_os,
            _ARISTA_EOS_NETWORK_OS,
        )
        return None

    def _resolve_credentials(
        self, hostname: str, merged: Dict[str, Any]
    ) -> Optional[ResolvedCredentials]:
        """Extract username and password from merged host variables."""
        username = merged.get("ansible_user")
        password = merged.get("ansible_password")

        if username is None or password is None:
            self.logger.warning(
                "Host %s is missing ansible_user / ansible_password — credentials unavailable",
                hostname,
            )
            return None

        return ResolvedCredentials(username=str(username), password=str(password))

    def _resolve_tls_verify(self, merged: Dict[str, Any]) -> Optional[bool]:
        """Resolve SSL certificate validation from merged host variables.

        ``ansible_httpapi_validate_certs`` is the canonical key.
        ``ansible_httpapi_use_ssl: false`` is invalid (HTTP eAPI not supported)
        and triggers a warning; the connection proceeds over HTTPS regardless.
        """
        use_ssl = merged.get("ansible_httpapi_use_ssl")
        if use_ssl is not None:
            coerced = self._coerce_bool(use_ssl, "ansible_httpapi_use_ssl")
            if coerced is False:
                self.logger.warning(
                    "ansible_httpapi_use_ssl=false is not supported; "
                    "avd-cli deploy eos always uses HTTPS (eAPI over SSL)"
                )

        validate_certs = merged.get("ansible_httpapi_validate_certs")
        if validate_certs is not None:
            return self._coerce_bool(validate_certs, "ansible_httpapi_validate_certs")

        return None

    def _resolve_address(self, merged: Dict[str, Any]) -> Optional[str]:
        """Return the device IP / FQDN from ``ansible_host``."""
        address = merged.get("ansible_host")
        if address is None:
            return None
        return str(address)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _coerce_bool(self, value: Any, field_name: str) -> Optional[bool]:
        """Coerce a YAML value to bool; return None when unrecognised."""
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
        self.logger.warning("Field '%s' has unexpected value %r — ignored", field_name, value)
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

        for candidate in ("inventory.yml", "inventory.yaml"):
            inventory_file = inventory_path / candidate
            if inventory_file.exists():
                return inventory_file

        if required:
            raise InvalidInventoryError(f"No inventory.yml or inventory.yaml found in {inventory_path}")
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
