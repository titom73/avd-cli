#!/usr/bin/env python
# coding: utf-8 -*-

"""Device filtering utilities.

This module provides filtering functionality for selecting devices
based on hostname or group name patterns using glob-style wildcards.
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from avd_cli.models.inventory import DeviceDefinition, InventoryData


@dataclass
class DeviceFilter:
    """Filter for selecting devices by hostname or group patterns.

    This class provides pattern-based filtering of devices using glob-style
    wildcards (*, ?, [...]) for matching hostnames or group names.

    Attributes
    ----------
    patterns : List[str]
        List of glob patterns for matching hostnames or groups
    """

    patterns: List[str]

    @classmethod
    def from_patterns(cls, patterns: Optional[List[str]]) -> Optional["DeviceFilter"]:
        """Create a DeviceFilter from CLI patterns.

        Parameters
        ----------
        patterns : Optional[List[str]]
            List of glob patterns for hostnames or groups.
            None or empty list returns None (no filtering).

        Returns
        -------
        Optional[DeviceFilter]
            DeviceFilter instance if patterns provided, None otherwise
        """
        if not patterns:
            return None

        # Remove empty strings and strip whitespace
        clean_patterns = [p.strip() for p in patterns if p.strip()]

        if not clean_patterns:
            return None

        return cls(patterns=clean_patterns)

    def matches_hostname(self, hostname: str) -> bool:
        """Check if hostname matches any pattern.

        Pattern matching is case-sensitive and uses glob-style wildcards:
        - * matches any number of characters
        - ? matches exactly one character
        - [...] matches any character in the brackets

        Parameters
        ----------
        hostname : str
            Device hostname to check

        Returns
        -------
        bool
            True if hostname matches any pattern, False otherwise
        """
        return any(fnmatch(hostname, pattern) for pattern in self.patterns)

    def matches_group(self, group: str) -> bool:
        """Check if group name matches any pattern.

        Pattern matching is case-sensitive and uses glob-style wildcards:
        - * matches any number of characters
        - ? matches exactly one character
        - [...] matches any character in the brackets

        Parameters
        ----------
        group : str
            Group name to check

        Returns
        -------
        bool
            True if group matches any pattern, False otherwise
        """
        return any(fnmatch(group, pattern) for pattern in self.patterns)

    def matches_device(self, hostname: str, groups: List[str]) -> bool:
        """Check if device matches filter by hostname OR group membership.

        A device matches if either:
        1. Its hostname matches any pattern, OR
        2. Any of its groups matches any pattern

        This implements a union (logical OR) of hostname and group matches,
        providing maximum flexibility for device selection.

        Parameters
        ----------
        hostname : str
            Device hostname
        groups : List[str]
            List of groups device belongs to (including fabric)

        Returns
        -------
        bool
            True if device matches by hostname or any group, False otherwise
        """
        # Check hostname match first
        if self.matches_hostname(hostname):
            return True

        # Check if any group matches
        return any(self.matches_group(group) for group in groups)

    def __repr__(self) -> str:
        """Return string representation of filter.

        Returns
        -------
        str
            String representation showing patterns
        """
        return f"DeviceFilter(patterns={self.patterns})"


def filter_devices(
    inventory: "InventoryData",
    device_filter: Optional[DeviceFilter] = None,
) -> List["DeviceDefinition"]:
    """Filter devices from inventory using optional DeviceFilter.

    This function provides a standardized way to filter devices from an
    inventory based on hostname or group patterns. It is used by both
    the configuration generator and topology generator.

    Parameters
    ----------
    inventory : InventoryData
        Loaded inventory data containing device definitions.
    device_filter : Optional[DeviceFilter], optional
        Filter to apply. If None, returns all devices.

    Returns
    -------
    List[DeviceDefinition]
        Filtered list of devices. Returns all devices if no filter provided.

    Examples
    --------
    >>> from avd_cli.utils.device_filter import DeviceFilter, filter_devices
    >>> device_filter = DeviceFilter.from_patterns(["leaf-*"])
    >>> filtered = filter_devices(inventory, device_filter)
    >>> print(f"Filtered to {len(filtered)} devices")
    """
    devices = inventory.get_all_devices()

    if device_filter is None:
        return devices

    return [
        device
        for device in devices
        if device_filter.matches_device(device.hostname, device.groups + [device.fabric])
    ]
