#!/usr/bin/env python
# coding: utf-8 -*-

"""Unit tests for helpers in ``avd_cli.cli.commands.generate``."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import List

import pytest

# Older package init expects deploy and validate modules which are not present.
sys.modules.setdefault("avd_cli.cli.commands.deploy", ModuleType("avd_cli.cli.commands.deploy"))
sys.modules.setdefault("avd_cli.cli.commands.validate", ModuleType("avd_cli.cli.commands.validate"))

# pylint: disable=wrong-import-position  # Import after sys.modules setup
from avd_cli.cli.commands import generate as generate_module  # noqa: E402


class InventoryLoaderStub:
    """Simple stub to capture inventory loading calls."""

    def __init__(self, inventory: "InventoryStub") -> None:
        self.inventory = inventory
        self.load_calls: List[Path] = []

    def load(self, inventory_path: Path):
        """Return the prepared inventory while tracking load invocations."""

        self.load_calls.append(inventory_path)
        return self.inventory


class InventoryStub:
    """Minimal inventory interface used by the helper tests."""

    def __init__(self, devices):
        self._devices = list(devices)

    def get_all_devices(self):
        """Return the fake devices provided to the stub."""

        return list(self._devices)


@pytest.fixture
def sample_inventory(monkeypatch, tmp_path):
    """Provide a stubbed inventory and patch the loader used by the module."""

    device = SimpleNamespace(hostname="leaf-1a", groups=["campus"], fabric="fabric-a")
    inventory = InventoryStub([device])
    loader = InventoryLoaderStub(inventory)
    monkeypatch.setattr(generate_module, "InventoryLoader", lambda: loader)

    inventory_path = tmp_path / "inventory"
    inventory_path.mkdir()

    return inventory_path, inventory, loader


def test_merge_patterns_returns_combined_list():
    """Ensure helper merges positional and legacy patterns preserving order."""

    combined = generate_module._merge_patterns(("leaf*",), ("spine*", "border*"))

    assert combined == ["leaf*", "spine*", "border*"]


def test_prepare_inventory_returns_filter(sample_inventory):
    """Verify inventory loading and device filtering succeed with matches."""

    inventory_path, inventory, loader = sample_inventory

    returned_inventory, device_filter = generate_module._prepare_inventory(
        inventory_path=inventory_path,
        all_patterns=["leaf-*"],
        verbose=True,
        show_deprecation_warnings=False,
    )

    assert returned_inventory is inventory
    assert loader.load_calls == [inventory_path]
    assert device_filter is not None
    assert device_filter.matches_device("leaf-1a", ["campus", "fabric-a"])


def test_prepare_inventory_without_patterns_returns_none(sample_inventory):
    """Ensure helper skips filter creation when no patterns are provided."""

    inventory_path, _, _ = sample_inventory

    returned_inventory, device_filter = generate_module._prepare_inventory(
        inventory_path=inventory_path,
        all_patterns=[],
        verbose=False,
        show_deprecation_warnings=True,
    )

    assert device_filter is None
    assert returned_inventory.get_all_devices()[0].hostname == "leaf-1a"


def test_prepare_inventory_exits_when_no_devices_match(sample_inventory):
    """Confirm helper exits early when filters exclude all devices."""

    inventory_path, _, _ = sample_inventory

    with pytest.raises(SystemExit) as exc_info:
        generate_module._prepare_inventory(
            inventory_path=inventory_path,
            all_patterns=["spine-*"],
            verbose=False,
            show_deprecation_warnings=False,
        )

    assert exc_info.value.code == 1
