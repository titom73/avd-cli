#!/usr/bin/env python
# coding: utf-8 -*-

"""Version utility functions for avd-cli and its dependencies."""


def get_pyavd_version() -> str:
    """Get the installed pyavd package version.

    Returns
    -------
    str
        The pyavd version string (e.g., "5.7.2"), "not installed" if pyavd
        is not available, or "unknown" if version cannot be determined.
    """
    try:
        import pyavd

        return getattr(pyavd, "__version__", "unknown")
    except ImportError:
        return "not installed"


def get_avd_cli_version() -> str:
    """Get the installed avd-cli package version.

    Returns
    -------
    str
        The avd-cli version string.
    """
    from avd_cli import __version__

    return __version__
