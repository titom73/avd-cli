#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for connection inventory multi-schema loader."""

from pathlib import Path

import pytest

from avd_cli.exceptions import InvalidInventoryError
from avd_cli.logics.connection_inventory_loader import ConnectionInventoryLoader


def _write_inventory(inventory_dir: Path, content: str) -> None:
    inventory_dir.mkdir(parents=True, exist_ok=True)
    (inventory_dir / "inventory.yml").write_text(content, encoding="utf-8")


def test_flat_schema_inherits_first_group_credentials(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals:
  credentials:
    username: arista
    password: arista
  tls_verify: true

groups:
  leaf_eos:
    kind: arista_eos
    tls_verify: false
    credentials:
      username: leaf_user
      password: leaf_pass
  demo:
    credentials:
      username: demo_user
      password: demo_pass

hosts:
  leaf1:
    address: 192.168.72.13
    groups:
      - leaf_eos
      - demo
""",
    )

    loader = ConnectionInventoryLoader()
    loaded = loader.load(inventory_dir, strict=True)

    assert loaded.schema == "flat"
    assert len(loaded.hosts) == 1
    host = loaded.hosts[0]
    assert host.hostname == "leaf1"
    assert host.kind == "arista_eos"
    assert host.tls_verify is False
    assert host.credentials is not None
    assert host.credentials.username == "leaf_user"
    assert host.credentials.password == "leaf_pass"


def test_flat_schema_credentials_fallback_to_globals(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals:
  kind: arista_eos
  credentials:
    username: global_user
    password: global_pass

groups:
  demo: {}

hosts:
  leaf1:
    address: 10.0.0.1
    groups:
      - demo
""",
    )

    loader = ConnectionInventoryLoader()
    loaded = loader.load(inventory_dir, strict=True)

    host = loaded.hosts[0]
    assert host.credentials is not None
    assert host.credentials.username == "global_user"
    assert host.credentials.password == "global_pass"


def test_flat_schema_partial_credentials_fallback_field_by_field(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals:
  kind: arista_eos
  credentials:
    username: global_user
    password: global_pass

groups:
  leaf:
    credentials:
      username: leaf_user

hosts:
  leaf1:
    address: 10.0.0.1
    groups:
      - leaf
""",
    )

    loader = ConnectionInventoryLoader()
    loaded = loader.load(inventory_dir, strict=True)
    host = loaded.hosts[0]
    assert host.credentials is not None
    assert host.credentials.username == "leaf_user"
    assert host.credentials.password == "global_pass"


def test_flat_schema_unknown_group_reference_fails(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals:
  kind: arista_eos
groups: {}
hosts:
  leaf1:
    address: 10.0.0.1
    groups:
      - missing_group
""",
    )

    loader = ConnectionInventoryLoader()
    with pytest.raises(InvalidInventoryError, match="unknown groups"):
        loader.load(inventory_dir, strict=True)


def test_flat_schema_missing_kind_fails_in_strict_mode(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals: {}
groups: {}
hosts:
  leaf1:
    address: 10.0.0.1
    credentials:
      username: user
      password: pass
""",
    )

    loader = ConnectionInventoryLoader()
    with pytest.raises(InvalidInventoryError, match="missing kind"):
        loader.load(inventory_dir, strict=True)


def test_detect_schema_ambiguous_mixed_top_level_keys_fails(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
globals: {}
groups: {}
hosts: {}
all: {}
""",
    )

    loader = ConnectionInventoryLoader()
    with pytest.raises(InvalidInventoryError, match="Ambiguous inventory schema"):
        loader.detect_schema(inventory_dir)


def test_ansible_schema_parsing_keeps_backward_compatibility(tmp_path: Path) -> None:
    inventory_dir = tmp_path / "inventory"
    _write_inventory(
        inventory_dir,
        """---
all:
  children:
    spines:
      vars:
        ansible_user: admin
        ansible_password: admin
      hosts:
        spine1:
          ansible_host: 192.0.2.10
""",
    )

    loader = ConnectionInventoryLoader()
    loaded = loader.load(inventory_dir, strict=True)

    assert loaded.schema == "ansible"
    assert len(loaded.hosts) == 1
    host = loaded.hosts[0]
    assert host.hostname == "spine1"
    assert host.kind == "arista_eos"
    assert host.groups == ["spines"]
    assert host.credentials is not None
    assert host.credentials.username == "admin"
    assert host.credentials.password == "admin"
