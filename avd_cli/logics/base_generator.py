#!/usr/bin/env python
# coding: utf-8 -*-

"""Base generator abstract class for AVD CLI.

This module provides an abstract base class for all AVD generators,
defining a common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from avd_cli.models.inventory import DeviceDefinition, InventoryData
    from avd_cli.utils.device_filter import DeviceFilter


class BaseGenerator(ABC):
    """Abstract base class for all AVD generators.

    Provides common functionality for configuration, documentation,
    ANTA test, and topology generators. All generators must inherit
    from this class and implement the generate() method.

    This base class enforces a consistent interface across all generators
    and provides shared utility methods for common operations like device
    filtering.
    """

    @abstractmethod
    def generate(
        self,
        inventory: "InventoryData",
        output_path: Path,
        device_filter: Optional["DeviceFilter"] = None,
    ) -> List[Path]:
        """Generate output files from inventory.

        This method must be implemented by all subclasses. It is responsible
        for generating the appropriate output files (configurations, documentation,
        tests, etc.) from the provided inventory data.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data containing device definitions and variables
        output_path : Path
            Directory where generated files should be written
        device_filter : Optional[DeviceFilter], optional
            Filter to limit generation to specific devices, by default None
            If None, all devices in the inventory will be processed.

        Returns
        -------
        List[Path]
            List of paths to generated files

        Examples
        --------
        >>> generator = MyGenerator()
        >>> files = generator.generate(
        ...     inventory=inventory,
        ...     output_path=Path("./output"),
        ...     device_filter=DeviceFilter.from_patterns(["leaf-*"])
        ... )
        >>> print(f"Generated {len(files)} files")
        """
        pass

    def _get_filtered_devices(
        self,
        inventory: "InventoryData",
        device_filter: Optional["DeviceFilter"] = None,
    ) -> List["DeviceDefinition"]:
        """Get devices from inventory, optionally filtered.

        This is a utility method for subclasses to easily retrieve devices
        from the inventory with optional filtering. It uses the shared
        filter_devices() function to ensure consistent filtering behavior
        across all generators.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data containing device definitions
        device_filter : Optional[DeviceFilter], optional
            Filter to apply. If None, returns all devices.

        Returns
        -------
        List[DeviceDefinition]
            Filtered list of devices. Returns all devices if no filter provided.

        Examples
        --------
        >>> devices = self._get_filtered_devices(inventory, device_filter)
        >>> print(f"Processing {len(devices)} devices")
        """
        from avd_cli.utils.device_filter import filter_devices

        return filter_devices(inventory, device_filter)
