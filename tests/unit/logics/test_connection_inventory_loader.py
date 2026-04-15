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
from avd_cli.models.connection_inventory import ConnectionInventory, ResolvedCredentials, ResolvedHostConnection


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


# ---------------------------------------------------------------------------
# T14 — all: null → empty inventory
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_null_all_group_returns_empty_inventory(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """When the 'all' key is explicitly null, the result is an empty inventory.

    Covers the False branch of ``if isinstance(all_group, dict)`` (L95->100)
    and the ``if not isinstance(group_data, dict): continue`` guard (L113).
    """
    inv_path = _write_inventory(tmp_path, "all: null\n")

    result = loader.load(inv_path)

    assert isinstance(result, ConnectionInventory)
    assert len(result.hosts) == 0


# ---------------------------------------------------------------------------
# T15 — hosts: null → no hosts extracted for that group
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_null_hosts_value_is_skipped(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A group whose 'hosts' key is explicitly null yields no hosts.

    Covers the False branch of ``if isinstance(hosts, dict)`` (L142->147).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              hosts: null
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 0


# ---------------------------------------------------------------------------
# T16 — Host appears in two different groups → groups list accumulated
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_host_in_two_different_groups_accumulates_membership(
    tmp_path: Path, loader: ConnectionInventoryLoader
) -> None:
    """A host discovered via two distinct group names accumulates both groups.

    Covers ``existing.groups.append(group_name)`` (L163).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            GROUP_A:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
            GROUP_B:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1, "leaf1 must be deduplicated to a single entry"
    host = result.hosts[0]
    assert "GROUP_A" in host.groups
    assert "GROUP_B" in host.groups


# ---------------------------------------------------------------------------
# T17 — children: null → no child recursion, hosts still extracted
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_null_children_value_host_still_extracted(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A group with 'children: null' still yields its direct hosts.

    Covers the False branch of ``if isinstance(children, dict)`` in
    ``_recurse_children`` (L213->223).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              children: null
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1
    assert result.hosts[0].hostname == "leaf1"


# ---------------------------------------------------------------------------
# T18 — Implicit nested groups (no 'children:' wrapper key)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_implicit_nested_groups_without_children_key(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Sub-groups nested directly inside a group (without a 'children:' key) are traversed.

    Covers the second loop in ``_recurse_children`` that processes implicit
    sub-groups (L226).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
          children:
            FABRIC:
              vars:
                ansible_network_os: arista.eos.eos
              LEAFS:
                hosts:
                  leaf1:
                    ansible_host: 10.0.0.1
        """,
    )

    result = loader.load(inv_path)

    assert len(result.hosts) == 1
    assert result.hosts[0].hostname == "leaf1"
    assert result.hosts[0].kind == "arista_eos"


# ---------------------------------------------------------------------------
# T19 — Missing credentials → warning logged, host still present with credentials=None
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_missing_credentials_emits_warning(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """A host with no ansible_user/ansible_password gets credentials=None plus a warning.

    Covers the credential-absent warning branch (L273-277).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
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
    host = result.hosts[0]
    assert host.hostname == "leaf1"
    assert host.credentials is None
    assert any("leaf1" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# T20 — ansible_httpapi_use_ssl: true → no warning
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ansible_httpapi_use_ssl_true_no_warning(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """ansible_httpapi_use_ssl: true does NOT emit a warning.

    Covers the ``if coerced is False`` False branch (L291->297).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_use_ssl: true
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
    use_ssl_warnings = [m for m in caplog.messages if "ansible_httpapi_use_ssl" in m]
    assert not use_ssl_warnings, "No warning expected when use_ssl=true"


# ---------------------------------------------------------------------------
# T21 — _coerce_bool: quoted string "yes" / "true" → True
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_coerce_bool_string_true_values(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """ansible_httpapi_validate_certs quoted as 'yes' coerces to True.

    Covers the string-true branch in ``_coerce_bool`` (L320-323).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: "yes"
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
# T22 — _coerce_bool: quoted string "no" / "false" → False
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_coerce_bool_string_false_values(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """ansible_httpapi_validate_certs quoted as 'no' coerces to False.

    Covers the string-false branch in ``_coerce_bool`` (L324-325).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: "no"
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
# T23 — _coerce_bool: unknown / unexpected value → warning + None
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_coerce_bool_unknown_value_emits_warning(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected value (integer) for a boolean field emits a warning and yields None.

    Covers the unknown-value branch in ``_coerce_bool`` (L326-327).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: 42
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    with caplog.at_level(logging.WARNING):
        result = loader.load(inv_path)

    assert result.hosts[0].tls_verify is None
    assert any("ansible_httpapi_validate_certs" in msg for msg in caplog.messages)


# ---------------------------------------------------------------------------
# T24 — Load from a file path directly (not a directory)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_load_from_file_path_directly(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """Passing an inventory.yml file path directly to load() works correctly.

    Covers the ``if inventory_path.is_file(): return inventory_path`` branch (L331).
    """
    inv_file = tmp_path / "inventory.yml"
    inv_file.write_text(
        textwrap.dedent(
            """
            all:
              vars:
                ansible_user: admin
                ansible_password: pass
              children:
                FABRIC:
                  hosts:
                    leaf1:
                      ansible_host: 10.0.0.1
            """
        )
    )

    result = loader.load(inv_file)

    assert len(result.hosts) == 1
    assert result.hosts[0].hostname == "leaf1"


# ---------------------------------------------------------------------------
# T25 — Non-existent path raises InvalidInventoryError
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_nonexistent_inventory_path_raises(loader: ConnectionInventoryLoader) -> None:
    """A path that does not exist raises InvalidInventoryError.

    Covers the non-existent-path error branch (L334-335).
    """
    with pytest.raises(InvalidInventoryError, match="does not exist"):
        loader.load(Path("/nonexistent/path/that/must/not/exist/avd_cli_test"))


# ---------------------------------------------------------------------------
# T26 — Invalid YAML content raises InvalidInventoryError
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_invalid_yaml_raises(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A file with invalid YAML syntax raises InvalidInventoryError.

    Covers the ``except yaml.YAMLError`` branch in ``_load_yaml_file`` (L354-355).
    """
    inv_file = tmp_path / "inventory.yml"
    inv_file.write_text("{ unclosed: yaml: [ bracket\n  bad: - indent\n")

    with pytest.raises(InvalidInventoryError, match="[Ii]nvalid YAML"):
        loader.load(tmp_path)


# ---------------------------------------------------------------------------
# T27 — Empty YAML file → empty inventory (no crash)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_empty_yaml_returns_empty_inventory(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """An empty inventory file yields an empty ConnectionInventory without raising.

    Covers the ``if loaded is None: return {}`` branch (L360).
    """
    inv_file = tmp_path / "inventory.yml"
    inv_file.write_text("")

    result = loader.load(tmp_path)

    assert isinstance(result, ConnectionInventory)
    assert len(result.hosts) == 0


# ---------------------------------------------------------------------------
# T28 — YAML root is a list (not a mapping) → raises InvalidInventoryError
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_yaml_list_root_raises(tmp_path: Path, loader: ConnectionInventoryLoader) -> None:
    """A YAML file whose root is a list (not a mapping) raises InvalidInventoryError.

    Covers the ``raise InvalidInventoryError("Inventory YAML root must be a mapping")``
    branch in ``_load_yaml_file`` (L362).
    """
    inv_file = tmp_path / "inventory.yml"
    inv_file.write_text("- item1\n- item2\n")

    with pytest.raises(InvalidInventoryError, match="mapping"):
        loader.load(tmp_path)


# ---------------------------------------------------------------------------
# T29 — _parse_ansible_inventory called with non-dict → raises (private API)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_ansible_inventory_non_dict_raises(loader: ConnectionInventoryLoader) -> None:
    """Calling _parse_ansible_inventory with a non-dict raises InvalidInventoryError.

    Covers the direct guard at L90 (dead code from public API, reachable via
    private method call).
    """
    with pytest.raises(InvalidInventoryError, match="mapping"):
        loader._parse_ansible_inventory(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# T30 — _coerce_bool(None, ...) returns None immediately (private API)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_coerce_bool_none_value_returns_none(loader: ConnectionInventoryLoader) -> None:
    """_coerce_bool returns None immediately when value is None.

    Covers the ``if value is None: return None`` early return at L317 (dead code
    from public API because callers guard with ``is not None``, reachable via
    private method call).
    """
    result = loader._coerce_bool(None, "test_field")  # type: ignore[arg-type]
    assert result is None


# ---------------------------------------------------------------------------
# T31 — ResolvedCredentials.masked() hides password
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_resolved_credentials_masked_hides_password() -> None:
    """ResolvedCredentials.masked() returns username in plain text and masked password.

    Covers lines 19-22 in connection_inventory.py.
    """
    creds = ResolvedCredentials(username="admin", password="s3cr3t!")
    masked = creds.masked()

    assert masked["username"] == "admin"
    assert masked["password"] == "*" * len("s3cr3t!")
    assert "s3cr3t!" not in masked["password"]


# ---------------------------------------------------------------------------
# T32 — ConnectionInventory.as_info_dict() builds safe payload
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_connection_inventory_as_info_dict() -> None:
    """ConnectionInventory.as_info_dict() returns a safe, sorted host payload.

    Covers lines 45-57 in connection_inventory.py.
    """
    creds = ResolvedCredentials(username="admin", password="topsecret")
    hosts = [
        ResolvedHostConnection(
            hostname="spine1",
            address="10.0.0.1",
            groups=["FABRIC"],
            kind="arista_eos",
            credentials=creds,
            tls_verify=True,
        ),
        ResolvedHostConnection(
            hostname="leaf1",
            address="10.0.0.10",
            groups=["LEAFS"],
            kind="arista_eos",
            credentials=None,
            tls_verify=False,
        ),
    ]
    inv = ConnectionInventory(hosts=hosts)

    info = inv.as_info_dict()

    assert info["total_hosts"] == 2
    # Result is sorted by hostname: leaf1 before spine1
    assert info["hosts"][0]["hostname"] == "leaf1"
    assert info["hosts"][1]["hostname"] == "spine1"
    # Credentials are masked for spine1
    assert info["hosts"][1]["credentials"]["password"] == "*" * len("topsecret")
    # No credentials for leaf1
    assert info["hosts"][0]["credentials"] is None


# ---------------------------------------------------------------------------
# T33 — _coerce_bool: string that is neither true nor false → warning + None
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_coerce_bool_unrecognised_string_emits_warning(
    tmp_path: Path, loader: ConnectionInventoryLoader, caplog: pytest.LogCaptureFixture
) -> None:
    """A string value that is neither a true-like nor false-like word emits a warning.

    Covers the fall-through from the false-string check to the warning at L326
    (branch 324->326).
    """
    inv_path = _write_inventory(
        tmp_path,
        """
        all:
          vars:
            ansible_user: admin
            ansible_password: pass
            ansible_httpapi_validate_certs: "maybe"
          children:
            FABRIC:
              hosts:
                leaf1:
                  ansible_host: 10.0.0.1
        """,
    )

    with caplog.at_level(logging.WARNING):
        result = loader.load(inv_path)

    assert result.hosts[0].tls_verify is None
    assert any("ansible_httpapi_validate_certs" in msg for msg in caplog.messages)
