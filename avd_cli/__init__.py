#!/usr/bin/env python
# coding: utf-8 -*-

"""AVD CLI - Command-line interface for Arista AVD inventory processing.

This package provides a CLI tool for processing Arista Ansible AVD inventories
and generating configurations, documentation, and ANTA tests using py-avd.
"""

__version__ = "0.1.0"
__author__ = "AVD CLI Development Team"
__license__ = "Apache-2.0"

from avd_cli.exceptions import AvdCliError

__all__ = ["__version__", "__author__", "__license__", "AvdCliError"]
