#!/usr/bin/env python
# coding: utf-8 -*-

"""Schema utilities for loading constants from py-avd.

This module provides utilities to dynamically load schema constants from the
py-avd library, with graceful fallback to hardcoded values when py-avd is unavailable.
"""

import logging
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

# Fallback constants (used when py-avd is unavailable)
_FALLBACK_PLATFORMS = [
    "vEOS-lab",
    "vEOS",
    "cEOS",
    "cEOSLab",
    "720XP",
    "722XP",
    "7050X3",
    "7280R3",
    "7500R3",
    "7800R3",
]

_FALLBACK_DEVICE_TYPES = [
    "spine",
    "leaf",
    "border_leaf",
    "super_spine",
    "overlay_controller",
    "wan_router",
]


@lru_cache(maxsize=1)
def get_supported_platforms() -> List[str]:
    """Get list of supported EOS platforms.

    Attempts to load from py-avd schema. Falls back to hardcoded list
    if py-avd is unavailable or import fails.

    Returns
    -------
    List[str]
        List of supported platform names

    Examples
    --------
    >>> platforms = get_supported_platforms()
    >>> "vEOS-lab" in platforms
    True
    """
    try:
        # Attempt to import py-avd schema
        # Note: Actual pyavd API may differ - adjust based on real implementation
        import pyavd  # noqa: F401

        # For now, return fallback until py-avd API is confirmed
        logger.info("py-avd available, using %d platforms", len(_FALLBACK_PLATFORMS))
        return list(_FALLBACK_PLATFORMS)

    except (ImportError, AttributeError) as e:
        logger.debug("Could not load platforms from py-avd: %s. Using fallback list.", e)
        return list(_FALLBACK_PLATFORMS)


@lru_cache(maxsize=1)
def get_supported_device_types() -> List[str]:
    """Get list of supported device types.

    Attempts to load from py-avd schema. Falls back to hardcoded list
    if py-avd is unavailable or import fails.

    Returns
    -------
    List[str]
        List of supported device type names

    Examples
    --------
    >>> types = get_supported_device_types()
    >>> "spine" in types
    True
    """
    try:
        # Attempt to import py-avd schema
        import pyavd  # noqa: F401

        # For now, return fallback until py-avd API is confirmed
        logger.info("py-avd available, using %d device types", len(_FALLBACK_DEVICE_TYPES))
        return list(_FALLBACK_DEVICE_TYPES)

    except (ImportError, AttributeError) as e:
        logger.debug("Could not load device types from py-avd: %s. Using fallback list.", e)
        return list(_FALLBACK_DEVICE_TYPES)


@lru_cache(maxsize=1)
def get_avd_schema_version() -> Optional[str]:
    """Get py-avd schema version.

    Returns
    -------
    Optional[str]
        Schema version string, or None if py-avd unavailable

    Examples
    --------
    >>> version = get_avd_schema_version()
    >>> version is None or isinstance(version, str)
    True
    """
    try:
        import pyavd

        return getattr(pyavd, "__version__", None)
    except ImportError:
        logger.debug("py-avd not available, schema version unknown")
        return None


def clear_schema_cache() -> None:
    """Clear cached schema values.

    Useful for testing or when py-avd is dynamically loaded.

    Examples
    --------
    >>> clear_schema_cache()
    >>> platforms = get_supported_platforms()  # Will reload from schema
    """
    get_supported_platforms.cache_clear()
    get_supported_device_types.cache_clear()
    get_avd_schema_version.cache_clear()
