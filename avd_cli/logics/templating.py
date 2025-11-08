#!/usr/bin/env python
# coding: utf-8 -*-

"""Jinja2 template resolution for AVD inventory variables.

This module provides functionality to resolve Jinja2 template variables
in AVD inventory YAML data structures, supporting Ansible-style variable
references and filters.
"""

import logging
import re
from typing import Any, Dict, List

from jinja2 import Environment, Undefined
from jinja2 import TemplateError as Jinja2TemplateError

from avd_cli.exceptions import TemplateError as AvdTemplateError

logger = logging.getLogger(__name__)


class TemplateResolver:
    """Resolve Jinja2 templates in AVD inventory data.

    This class handles resolution of Jinja2 template variables following
    Ansible conventions for variable references, hostvars access, and filters.

    Parameters
    ----------
    context : Dict[str, Any]
        Template context containing all variables available for resolution

    Examples
    --------
    >>> context = {
    ...     "default_mtu": 9214,
    ...     "hostvars": {"spine01": {"platform": "7050X3"}}
    ... }
    >>> resolver = TemplateResolver(context)
    >>> resolver.resolve("{{ default_mtu }}")
    '9214'
    >>> resolver.resolve("{{ hostvars['spine01']['platform'] }}")
    '7050X3'
    """

    # Pattern to detect both Jinja2 variables {{ }} and statements {% %}
    TEMPLATE_PATTERN = re.compile(r'\{\{.*?\}\}|\{%.*?%\}')

    def __init__(self, context: Dict[str, Any]) -> None:
        """Initialize template resolver with context.

        Parameters
        ----------
        context : Dict[str, Any]
            Variables available for template resolution
        """
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Create Jinja2 environment with default undefined behavior
        # (undefined variables render as empty string instead of raising error)
        self.env = Environment(
            variable_start_string='{{',
            variable_end_string='}}',
            undefined=Undefined,
            autoescape=False,
        )

        # Add custom filters (Ansible-compatible)
        self.env.filters['bool'] = self._filter_bool

    @staticmethod
    def _filter_bool(value: Any) -> bool:
        """Convert value to boolean (Ansible-style).

        Parameters
        ----------
        value : Any
            Value to convert

        Returns
        -------
        bool
            Boolean representation
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('yes', 'true', '1', 'on')
        return bool(value)

    def has_template(self, value: str) -> bool:
        """Check if string contains Jinja2 template syntax.

        Parameters
        ----------
        value : str
            String to check

        Returns
        -------
        bool
            True if string contains {{ ... }} templates
        """
        return bool(self.TEMPLATE_PATTERN.search(value))

    def resolve(self, template_str: str) -> str:
        """Resolve a single template string.

        Parameters
        ----------
        template_str : str
            String containing Jinja2 template(s)

        Returns
        -------
        str
            Resolved string with templates replaced by their values

        Raises
        ------
        TemplateError
            If template resolution fails (undefined variable, syntax error, etc.)

        Examples
        --------
        >>> resolver = TemplateResolver({"mtu": 9214})
        >>> resolver.resolve("{{ mtu }}")
        '9214'
        >>> resolver.resolve("{{ mtu | default(1500) }}")
        '9214'
        """
        # If no template syntax, return as-is
        if not self.has_template(template_str):
            return template_str

        try:
            template = self.env.from_string(template_str)
            result = template.render(self.context)
            self.logger.debug("Resolved template '%s' to '%s'", template_str, result)
            return result
        except Jinja2TemplateError as e:
            error_msg = f"Template error: {e}"
            self.logger.error(error_msg)
            raise AvdTemplateError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error resolving template '{template_str}': {e}"
            self.logger.error(error_msg)
            raise AvdTemplateError(error_msg) from e

    def resolve_value(self, value: Any) -> Any:
        """Resolve templates in a single value (string, int, bool, etc.).

        Only string values are processed for templates. Other types are returned
        unchanged to preserve type information.

        Parameters
        ----------
        value : Any
            Value to resolve (string, int, bool, None, etc.)

        Returns
        -------
        Any
            Resolved value (same type as input for non-strings)

        Examples
        --------
        >>> resolver = TemplateResolver({"mtu": 9214})
        >>> resolver.resolve_value("{{ mtu }}")
        '9214'
        >>> resolver.resolve_value(123)
        123
        >>> resolver.resolve_value(True)
        True
        """
        # Only resolve templates in strings
        if isinstance(value, str):
            return self.resolve(value)
        return value

    def resolve_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve templates in a dictionary.

        Walks through the dictionary structure recursively, resolving templates
        in all string values while preserving the structure and non-string types.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing potential templates

        Returns
        -------
        Dict[str, Any]
            Dictionary with all templates resolved

        Examples
        --------
        >>> context = {"server": "10.0.0.100", "vrf": "MGMT"}
        >>> resolver = TemplateResolver(context)
        >>> data = {"radius": {"host": "{{ server }}", "vrf": "{{ vrf }}"}}
        >>> resolved = resolver.resolve_dict(data)
        >>> resolved["radius"]["host"]
        '10.0.0.100'
        """
        result = {}
        for key, value in data.items():
            result[key] = self.resolve_recursive(value)
        return result

    def resolve_list(self, data: List[Any]) -> List[Any]:
        """Recursively resolve templates in a list.

        Parameters
        ----------
        data : List[Any]
            List containing potential templates

        Returns
        -------
        List[Any]
            List with all templates resolved
        """
        return [self.resolve_recursive(item) for item in data]

    def resolve_recursive(self, data: Any) -> Any:
        """Recursively resolve templates in any data structure.

        This method handles dicts, lists, and primitive types, recursively
        walking through nested structures to resolve all template strings.

        Parameters
        ----------
        data : Any
            Data structure (dict, list, str, int, bool, None, etc.)

        Returns
        -------
        Any
            Data structure with all templates resolved

        Examples
        --------
        >>> context = {"mtu": 9214, "vrf": "MGMT"}
        >>> resolver = TemplateResolver(context)
        >>> data = {
        ...     "interfaces": [
        ...         {"name": "Ethernet1", "mtu": "{{ mtu }}"},
        ...         {"name": "Ethernet2", "mtu": "{{ mtu }}"}
        ...     ],
        ...     "vrf": "{{ vrf }}"
        ... }
        >>> resolved = resolver.resolve_recursive(data)
        >>> resolved["interfaces"][0]["mtu"]
        '9214'
        """
        if isinstance(data, dict):
            return self.resolve_dict(data)
        if isinstance(data, list):
            return self.resolve_list(data)
        if isinstance(data, str):
            return self.resolve(data)
        # Preserve non-string types (int, bool, None, etc.)
        return data


def build_template_context(
    global_vars: Dict[str, Any],
    group_vars: Dict[str, Dict[str, Any]],
    host_vars: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Build Jinja2 template context from inventory variables.

    Creates a context dictionary suitable for template resolution by merging
    global variables, group variables, and constructing the hostvars dictionary.

    For hostvars, we merge global + all group vars + host vars for each host.
    This ensures templates like {{ hostvars['host']['group_var'] }} work.

    Parameters
    ----------
    global_vars : Dict[str, Any]
        Global variables from group_vars/all.yml
    group_vars : Dict[str, Dict[str, Any]]
        All group variables
    host_vars : Dict[str, Dict[str, Any]]
        All host variables

    Returns
    -------
    Dict[str, Any]
        Template context with all variables and hostvars

    Examples
    --------
    >>> global_vars = {"default_mtu": 9214}
    >>> group_vars = {"SPINES": {"bgp_as": 65001}}
    >>> host_vars = {"spine01": {"platform": "7050X3"}}
    >>> context = build_template_context(global_vars, group_vars, host_vars)
    >>> context["default_mtu"]
    9214
    >>> context["hostvars"]["spine01"]["platform"]
    '7050X3'
    """
    context: Dict[str, Any] = {}

    # Add global variables
    context.update(global_vars)

    # Add all group variables (later groups may override earlier ones)
    for group_data in group_vars.values():
        context.update(group_data)

    # Create enriched hostvars dictionary (Ansible-style)
    # Each host gets: global_vars + its host_vars
    # We intentionally do NOT merge all group_vars here because we don't know
    # which groups each host belongs to without parsing inventory.yml hierarchy.
    # Group vars are available at the top level of the context for direct access.
    enriched_hostvars: Dict[str, Dict[str, Any]] = {}

    # For each host, merge global vars + host vars
    for hostname, host_data in host_vars.items():
        enriched_hostvars[hostname] = {**global_vars, **host_data}
        # Add special Ansible variables
        enriched_hostvars[hostname]["inventory_hostname"] = hostname

    context["hostvars"] = enriched_hostvars

    logger.debug("Built template context with %d top-level keys and %d hosts",
                 len(context), len(enriched_hostvars))
    return context
