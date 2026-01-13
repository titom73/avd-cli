#!/usr/bin/env python
# coding: utf-8 -*-

"""Utility functions package initialization."""

from avd_cli.utils.package_manager import (
    InstallResult,
    PackageManager,
    PackageManagerType,
    is_uv_managed_project,
)
from avd_cli.utils.schema import (
    clear_schema_cache,
    get_avd_schema_version,
    get_supported_device_types,
    get_supported_platforms,
)
from avd_cli.utils.version import get_avd_cli_version, get_pyavd_version

__all__ = [
    "get_supported_platforms",
    "get_supported_device_types",
    "get_avd_schema_version",
    "clear_schema_cache",
    "get_pyavd_version",
    "get_avd_cli_version",
    "PackageManager",
    "PackageManagerType",
    "InstallResult",
    "is_uv_managed_project",
]
