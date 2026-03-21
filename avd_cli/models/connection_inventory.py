#!/usr/bin/env python
# coding: utf-8 -*-

"""Connection-oriented inventory models for deployment and inspection commands."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ResolvedCredentials:
    """Resolved device credentials."""

    username: str
    password: str

    def masked(self) -> Dict[str, str]:
        """Return a masked representation safe for display."""
        return {
            "username": self.username,
            "password": "*" * len(self.password),
        }


@dataclass
class ResolvedHostConnection:
    """Resolved per-host connection data."""

    hostname: str
    address: Optional[str]
    groups: List[str] = field(default_factory=list)
    kind: Optional[str] = None
    credentials: Optional[ResolvedCredentials] = None
    tls_verify: Optional[bool] = None


@dataclass
class ConnectionInventory:
    """Connection inventory normalized from either supported input schema."""

    schema: str
    hosts: List[ResolvedHostConnection] = field(default_factory=list)
    globals_data: Dict[str, Any] = field(default_factory=dict)
    groups_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def as_info_dict(self) -> Dict[str, Any]:
        """Build a safe dictionary payload for info command output."""
        hosts = []
        for host in sorted(self.hosts, key=lambda item: item.hostname):
            hosts.append(
                {
                    "hostname": host.hostname,
                    "address": host.address,
                    "groups": host.groups,
                    "kind": host.kind,
                    "tls_verify": host.tls_verify,
                    "credentials": host.credentials.masked() if host.credentials else None,
                }
            )

        return {
            "schema": self.schema,
            "total_hosts": len(self.hosts),
            "hosts": hosts,
        }
