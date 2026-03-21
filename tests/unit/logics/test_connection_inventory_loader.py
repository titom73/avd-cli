#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for ConnectionInventoryLoader — Ansible standard model."""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path

import pytest

from avd_cli.exceptions import InvalidInventoryError
from avd_cli.logics.connection_inventory_loader import ConnectionInventoryLoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def loader() -> ConnectionInventoryLoader:
    return ConnectionInventoryLoader()


def _write_inventory(tmp_path: Path, content: str) -> Path:
    """Write an inventory.yml in *tmp_path* and return the directory path."""
    inv = tmp_path / "inventory.yml"
    inv.write_text(textwrap.dedent(content))
    return tmp_path


# ---------------------------------------------------------------------------
# T1 — Basic happy path
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_simple_ansible_inventory_resolves_credentials(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Basic Ansible inventory: vars at all level, single group, single host."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: secret
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 192.168.1.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1
    host = result.hosts[0]
    assert host.hostname == "leaf1"
    assert host.address == "192.168.1.1"
    assert host.credentials is not None
    assert host.credentials.username == "admin"
    assert host.credentials.password == "secret"
    assert host.kind == "arista_eos"


# ---------------------------------------------------------------------------
# T2 — Variable inheritance: group vars → hosts
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_group_vars_inherited_by_hosts(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Vars defined at group level are visible to hosts in that group."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          children:
            FABRIC:
              vars:
                ansible_user: fabric_user
                ansible_password: fabric_pass
              hosts:
                spine1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    host = result.hosts[0]
    assert host.credentials is not None
    assert host.credentials.username == "fabric_user"
    assert host.credentials.password == "fabric_pass"


# ---------------------------------------------------------------------------
# T3 — Host vars override group vars
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_host_vars_override_group_vars(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Host-level variables take precedence over group-level variables."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          children:
            FABRIC:
              vars:
                ansible_user: group_user
                ansible_password: group_pass
              hosts:
                leaf1:
                  ansible_host: 10.0.0.10
                  ansible_user: host_user
                  ansible_password: host_pass
        """,
    )

    result = loader.load(inv_path)

    host = result.hosts[0]
    assert host.credentials is not None
    assert host.credentials.username == "host_user"
    assert host.credentials.password == "host_pass"


# ---------------------------------------------------------------------------
# T4 — Multi-group deduplication
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_multi_group_deduplication(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A host referenced via multiple parent groups appears exactly once.

    Groups are accumulated; connection data from first encounter is kept.
    This mirrors the typical AVD pattern where ATD_LEAFS is nested under
    ATD_FABRIC, ATD_TENANTS_NETWORKS, and ATD_SERVERS simultaneously.
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            ATD_FABRIC:
              children:
                ATD_LEAFS:
                  hosts:
                    leaf1:
                      ansible_host: 192.168.0.1
            ATD_TENANTS_NETWORKS:
              children:
                ATD_LEAFS:
                  hosts:
                    leaf1:
                      ansible_host: 192.168.0.1
            ATD_SERVERS:
              children:
                ATD_LEAFS:
                  hosts:
                    leaf1:
                      ansible_host: 192.168.0.1
        """,
    )

    result = loader.load(inv_path)

    hostnames = [h.hostname for h in result.hosts]
    assert hostnames.count("leaf1") == 1, "leaf1 should appear exactly once after deduplication"
    host = result.hosts[0]
    assert "ATD_LEAFS" in host.groups


# ---------------------------------------------------------------------------
# T5 — ansible_network_os: arista.eos.eos → included
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_network_os_eos_is_included(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Hosts with ansible_network_os=arista.eos.eos are included with kind=arista_eos."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_network_os: arista.eos.eos
          children:
            FABRIC:
              hosts:
                eos_host:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1
    assert result.hosts[0].kind == "arista_eos"


# ---------------------------------------------------------------------------
# T6 — ansible_network_os: cisco.ios.ios → skipped
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_network_os_non_eos_is_skipped(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Hosts with a non-EOS ansible_network_os are excluded with a warning."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              hosts:
                ios_host:
                  ansible_host: 10.0.0.1
                  ansible_network_os: cisco.ios.ios
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 0


# ---------------------------------------------------------------------------
# T7 — ansible_network_os absent → defaults to arista_eos
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_network_os_absent_defaults_to_eos(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Absence of ansible_network_os defaults to arista_eos for backward compatibility."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              hosts:
                device1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1
    assert result.hosts[0].kind == "arista_eos"


# ---------------------------------------------------------------------------
# T8 — ansible_httpapi_validate_certs: false
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_httpapi_validate_certs_false(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """ansible_httpapi_validate_certs: false maps to tls_verify=False."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: false
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert result.hosts[0].tls_verify is False


# ---------------------------------------------------------------------------
# T9 — ansible_httpapi_validate_certs: true
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_httpapi_validate_certs_true(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """ansible_httpapi_validate_certs: true maps to tls_verify=True."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: true
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert result.hosts[0].tls_verify is True


# ---------------------------------------------------------------------------
# T10 — ansible_httpapi_use_ssl: false → warning, host still included
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_httpapi_use_ssl_false_emits_warning(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """ansible_httpapi_use_ssl: false triggers a warning; host is still included."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_use_ssl: false
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    with caplog.at_level(logging.WARNING):
        result = loader.load(inv_path)

    assert len(result.hosts) == 1
    assert any("ansible_httpapi_use_ssl" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# T11 — Host missing ansible_host is skipped with a warning
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_host_missing_address_is_skipped(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """A host without ansible_host is silently skipped (warning only, no exception)."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              hosts:
                no_address_host: {}
        """,
    )

    with caplog.at_level(logging.WARNING):
        result = loader.load(inv_path)

    assert len(result.hosts) == 0
    assert any("no_address_host" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# T12 — Nested children hierarchy resolves correctly
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_children_hierarchy_resolved(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Deeply nested children groups inherit vars and resolve hosts correctly."""
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: root_user
            ansible_password: root_pass
          children:
            DC1:
              vars:
                ansible_httpapi_validate_certs: false
              children:
                DC1_LEAFS:
                  hosts:
                    dc1_leaf1:
                      ansible_host: 172.16.0.1
                    dc1_leaf2:
                      ansible_host: 172.16.0.2
        """,
    )

    result = loader.load(inv_path)

    hostnames = {h.hostname for h in result.hosts}
    assert hostnames == {"dc1_leaf1", "dc1_leaf2"}
    for host in result.hosts:
        assert host.credentials is not None
        assert host.credentials.username == "root_user"
        assert host.tls_verify is False


# ---------------------------------------------------------------------------
# T13 — Directory with no inventory.yml raises
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_directory_inventory_no_yaml_raises(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A directory with no inventory.yml raises InvalidInventoryError."""
    with pytest.raises(InvalidInventoryError, match="No inventory"):
        loader.load(tmp_path)
