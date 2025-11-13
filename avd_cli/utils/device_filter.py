"""Device filtering utilities using pattern matching.

This module provides device filtering capabilities based on hostname, groups,
and fabric name using Ansible-compatible pattern matching.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Set

from avd_cli.utils.pattern_matcher import PatternMatcher

if TYPE_CHECKING:
    from avd_cli.models.inventory import DeviceDefinition

logger = logging.getLogger(__name__)


class DeviceFilter:
    """Filter devices based on limit patterns.

    Filters devices by matching patterns against:
    - Device hostname
    - Any of the device's inventory groups
    - Device fabric name

    A device matches if the pattern matches ANY of these fields (OR logic).

    Examples
    --------
    >>> devices = [device1, device2, device3]  # List of DeviceDefinition
    >>> filter = DeviceFilter(["spine*", "!spine01"])
    >>> filtered = filter.filter_devices(devices)
    """

    def __init__(self, limit_patterns: Optional[List[str]] = None) -> None:
        """Initialize device filter with limit patterns.

        Parameters
        ----------
        limit_patterns : Optional[List[str]], optional
            List of patterns to limit devices. If None or empty, all devices
            pass the filter.

        Raises
        ------
        ValueError
            If any pattern is invalid.
        """
        self.limit_patterns = limit_patterns or []
        self.pattern_matcher: Optional[PatternMatcher] = None

        if self.limit_patterns:
            self.pattern_matcher = PatternMatcher(self.limit_patterns)

    def filter_devices(self, devices: List[DeviceDefinition]) -> List[DeviceDefinition]:
        """Filter devices based on limit patterns.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices to filter.

        Returns
        -------
        List[DeviceDefinition]
            Filtered list of devices that match the patterns.

        Raises
        ------
        ValueError
            If patterns are specified but no devices match any pattern.
        """
        # If no limit patterns, return all devices
        if not self.pattern_matcher:
            return devices

        # Filter devices
        filtered_devices = [
            device for device in devices
            if self._device_matches(device)
        ]

        # Validate that all patterns matched at least one device
        self._validate_patterns_matched(devices)

        logger.info(
            "Filtered to %d devices (from %d total) using patterns: %s",
            len(filtered_devices),
            len(devices),
            self.limit_patterns
        )

        return filtered_devices

    def _device_matches(self, device: DeviceDefinition) -> bool:
        """Check if a device matches the limit patterns.

        A device matches if ANY of the following match:
        - Device hostname
        - Any of the device's groups
        - Device fabric

        Parameters
        ----------
        device : DeviceDefinition
            Device to check.

        Returns
        -------
        bool
            True if device matches, False otherwise.
        """
        if not self.pattern_matcher:
            return True

        # Check hostname
        if self.pattern_matcher.matches(device.hostname):
            return True

        # Check any group
        for group in device.groups:
            if self.pattern_matcher.matches(group):
                return True

        # Check fabric
        if self.pattern_matcher.matches(device.fabric):
            return True

        return False

    def _collect_matchable_values(self, devices: List[DeviceDefinition]) -> Set[str]:
        """Collect all matchable values from devices."""
        all_matchable_values: Set[str] = set()
        for device in devices:
            all_matchable_values.add(device.hostname)
            all_matchable_values.update(device.groups)
            all_matchable_values.add(device.fabric)
        return all_matchable_values

    def _find_unmatched_patterns(self, all_matchable_values: Set[str]) -> List[str]:
        """Find patterns that didn't match any values."""
        if not self.pattern_matcher or not self.pattern_matcher.inclusion_patterns:
            return []

        unmatched_patterns = []
        for pattern in self.pattern_matcher.inclusion_patterns:
            pattern_matcher = PatternMatcher([pattern])
            matched_values = pattern_matcher.get_matched_values(list(all_matchable_values))
            if not matched_values:
                unmatched_patterns.append(pattern)
        return unmatched_patterns

    def _build_suggestions(self, devices: List[DeviceDefinition]) -> List[str]:
        """Build suggestions for available devices."""
        suggestions = []
        available_hostnames = {device.hostname for device in devices}
        available_groups: Set[str] = set()
        available_fabrics = {device.fabric for device in devices}

        for device in devices:
            available_groups.update(device.groups)

        if available_hostnames:
            suggestions.append(f"  Available hostnames: {', '.join(sorted(available_hostnames)[:10])}")
            if len(available_hostnames) > 10:
                suggestions.append(f"    ... and {len(available_hostnames) - 10} more")

        if available_groups:
            suggestions.append(f"  Available groups: {', '.join(sorted(available_groups)[:10])}")
            if len(available_groups) > 10:
                suggestions.append(f"    ... and {len(available_groups) - 10} more")

        if available_fabrics:
            suggestions.append(f"  Available fabrics: {', '.join(sorted(available_fabrics))}")

        return suggestions

    def _validate_patterns_matched(self, devices: List[DeviceDefinition]) -> None:
        """Validate that all patterns matched at least one device.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of all devices to check against.

        Raises
        ------
        ValueError
            If any inclusion pattern did not match any device.
        """
        if not self.pattern_matcher or not self.pattern_matcher.inclusion_patterns:
            return

        all_matchable_values = self._collect_matchable_values(devices)
        unmatched_patterns = self._find_unmatched_patterns(all_matchable_values)

        if unmatched_patterns:
            error_msg = f"The following limit pattern(s) did not match any devices: {', '.join(unmatched_patterns)}"
            suggestions = self._build_suggestions(devices)

            if suggestions:
                error_msg += "\n\n" + "\n".join(suggestions)

            raise ValueError(error_msg)

    def get_matched_devices_summary(self, devices: List[DeviceDefinition]) -> dict[str, List[str]]:
        """Get summary of which patterns matched which devices.

        Useful for debugging and logging purposes.

        Parameters
        ----------
        devices : List[DeviceDefinition]
            List of devices to analyze.

        Returns
        -------
        dict[str, List[str]]
            Dictionary mapping pattern -> list of matched hostnames.
        """
        if not self.pattern_matcher:
            return {}

        summary: dict[str, List[str]] = {}

        for pattern in self.pattern_matcher.inclusion_patterns:
            pattern_matcher = PatternMatcher([pattern])
            matched_hostnames = []

            for device in devices:
                # Check if this device matches this specific pattern
                if pattern_matcher.matches(device.hostname):
                    matched_hostnames.append(device.hostname)
                    continue

                for group in device.groups:
                    if pattern_matcher.matches(group):
                        matched_hostnames.append(device.hostname)
                        break
                else:
                    if pattern_matcher.matches(device.fabric):
                        matched_hostnames.append(device.hostname)

            summary[pattern] = sorted(matched_hostnames)

        return summary

    def __repr__(self) -> str:
        """Return string representation of DeviceFilter."""
        return f"DeviceFilter(patterns={self.limit_patterns})"
